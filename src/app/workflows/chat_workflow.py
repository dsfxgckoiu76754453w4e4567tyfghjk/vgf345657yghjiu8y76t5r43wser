"""
Temporal workflow for chat message processing.

This workflow orchestrates the complete RAG pipeline:
1. Intent classification
2. Context retrieval (if needed)
3. Response generation
4. Caching

Benefits over Celery:
- Durable execution (survives worker crashes)
- Automatic retries per activity
- Workflow versioning
- Better observability
- Query workflow state in real-time
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional
from uuid import UUID

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging import get_logger
from app.services.intent_detector import IntentDetector, IntentType
from app.services.document_service import DocumentService
from app.services.langgraph_service import get_langgraph_service
from app.services.response_cache_service import response_cache_service
from app.services.enhanced_chat_service import EnhancedChatService

logger = get_logger(__name__)

# Create async engine for activities
async_engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ChatWorkflowInput:
    """Input for chat workflow."""
    user_id: str
    conversation_id: str
    message: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    enable_caching: bool = True


@dataclass
class IntentClassificationResult:
    """Result from intent classification activity."""
    primary_intent: str
    requires_rag: bool
    requires_tools: list[str]
    confidence: float


@dataclass
class RetrievalResult:
    """Result from retrieval activity."""
    chunks: list[dict[str, Any]]
    context: str
    sources: list[dict[str, Any]]


@dataclass
class GenerationResult:
    """Result from generation activity."""
    response: str
    tokens_used: int
    model_used: str
    cache_hit: bool


@dataclass
class ChatWorkflowResult:
    """Final workflow result."""
    response: str
    intent: str
    sources: list[dict[str, Any]]
    tokens_used: int
    model_used: str
    from_cache: bool
    workflow_id: str


# ============================================================================
# ACTIVITIES
# ============================================================================

@activity.defn(name="check_response_cache")
async def check_response_cache_activity(query: str, user_id: str) -> Optional[dict]:
    """
    Check if response is cached.
    
    Activity timeout: 30 seconds
    Retries: 2 (cache lookup should be fast)
    """
    try:
        logger.info(
            "cache_check_started",
            query=query[:50],
            user_id=user_id,
        )
        
        # Check cache
        cached = await response_cache_service.get_cached_response(
            query=query,
            user_id=UUID(user_id) if user_id else None,
        )
        
        if cached:
            logger.info(
                "cache_hit",
                query=query[:50],
                similarity=cached.similarity_score,
                tokens_saved=cached.tokens_saved,
            )
            return {
                "response": cached.response,
                "intent": cached.intent,
                "sources": cached.sources,
                "tokens_saved": cached.tokens_saved,
                "similarity": cached.similarity_score,
            }
        
        logger.info("cache_miss", query=query[:50])
        return None
        
    except Exception as e:
        logger.error(
            "cache_check_failed",
            query=query[:50],
            error=str(e),
        )
        # Don't fail workflow on cache errors
        return None


@activity.defn(name="classify_intent")
async def classify_intent_activity(message: str, user_id: str) -> IntentClassificationResult:
    """
    Classify user intent using IntentDetector.
    
    Activity timeout: 30 seconds
    Retries: 3
    """
    try:
        logger.info(
            "intent_classification_started",
            message=message[:50],
            user_id=user_id,
        )
        
        # Detect intents
        intent_detector = IntentDetector()
        intents = await intent_detector.detect_intents(message)
        
        # Determine primary intent and requirements
        if intents:
            primary = intents[0]
            primary_intent = primary.intent_type.value
            confidence = primary.confidence
            
            # Check if RAG is needed
            requires_rag = any(
                i.intent_type in [IntentType.DOCUMENT_SEARCH, IntentType.QUESTION_ANSWER]
                for i in intents
            )
            
            # Collect required tools
            requires_tools = []
            for intent in intents:
                if intent.intent_type == IntentType.IMAGE_GENERATION:
                    requires_tools.append("image_generation")
                elif intent.intent_type in [IntentType.WEB_SEARCH, IntentType.DEEP_WEB_SEARCH]:
                    requires_tools.append("web_search")
                elif intent.intent_type == IntentType.AUDIO_TRANSCRIPTION:
                    requires_tools.append("audio_transcription")
        else:
            primary_intent = "conversation"
            confidence = 0.5
            requires_rag = False
            requires_tools = []
        
        result = IntentClassificationResult(
            primary_intent=primary_intent,
            requires_rag=requires_rag,
            requires_tools=requires_tools,
            confidence=confidence,
        )
        
        logger.info(
            "intent_classification_completed",
            message=message[:50],
            primary_intent=primary_intent,
            requires_rag=requires_rag,
            confidence=confidence,
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "intent_classification_failed",
            message=message[:50],
            error=str(e),
        )
        raise


@activity.defn(name="retrieve_context")
async def retrieve_context_activity(
    query: str,
    user_id: str,
    intent: str,
) -> RetrievalResult:
    """
    Retrieve relevant context from vector DB.
    
    Activity timeout: 60 seconds
    Retries: 3
    """
    try:
        logger.info(
            "context_retrieval_started",
            query=query[:50],
            user_id=user_id,
            intent=intent,
        )
        
        # Get database session
        async with async_session_maker() as db:
            # Use DocumentService for semantic search
            doc_service = DocumentService(db)
            
            chunks = await doc_service.semantic_search(
                query=query,
                limit=5,
                user_id=UUID(user_id) if user_id else None,
                min_score=0.7,
            )
            
            # Format results
            formatted_chunks = [
                {
                    "content": chunk.content,
                    "source": chunk.document.title if hasattr(chunk, 'document') else "Unknown",
                    "score": getattr(chunk, 'score', 0.0),
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ]
            
            # Build context string
            context = "\n\n---\n\n".join([
                f"Source: {c['source']} (Relevance: {c['score']:.2%})\n{c['content']}"
                for c in formatted_chunks
            ])
            
            result = RetrievalResult(
                chunks=formatted_chunks,
                context=context,
                sources=formatted_chunks,
            )
            
            logger.info(
                "context_retrieval_completed",
                query=query[:50],
                chunks_count=len(formatted_chunks),
                avg_score=sum(c['score'] for c in formatted_chunks) / len(formatted_chunks) if formatted_chunks else 0,
            )
            
            return result
            
    except Exception as e:
        logger.error(
            "context_retrieval_failed",
            query=query[:50],
            error=str(e),
        )
        # Return empty result on failure
        return RetrievalResult(chunks=[], context="", sources=[])


@activity.defn(name="generate_response")
async def generate_response_activity(
    message: str,
    context: str,
    intent: str,
    user_id: str,
    conversation_id: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> GenerationResult:
    """
    Generate response using LLM.
    
    Activity timeout: 5 minutes (LLM calls can be slow)
    Retries: 3
    """
    try:
        logger.info(
            "response_generation_started",
            message=message[:50],
            has_context=bool(context),
            intent=intent,
        )
        
        # Get database session
        async with async_session_maker() as db:
            # Use EnhancedChatService
            chat_service = EnhancedChatService(db)
            
            # Generate response
            response = await chat_service.generate_response(
                user_id=UUID(user_id),
                conversation_id=UUID(conversation_id),
                message=message,
                context=context if context else None,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            result = GenerationResult(
                response=response.get("response", ""),
                tokens_used=response.get("tokens_used", 0),
                model_used=response.get("model_used", model or settings.llm_model),
                cache_hit=response.get("cache_hit", False),
            )
            
            logger.info(
                "response_generation_completed",
                message=message[:50],
                tokens_used=result.tokens_used,
                model=result.model_used,
                response_length=len(result.response),
            )
            
            return result
            
    except Exception as e:
        logger.error(
            "response_generation_failed",
            message=message[:50],
            error=str(e),
        )
        raise


@activity.defn(name="cache_response")
async def cache_response_activity(
    query: str,
    response: str,
    intent: str,
    sources: list[dict],
    tokens_used: int,
    user_id: str,
    conversation_id: str,
) -> bool:
    """
    Cache the generated response.
    
    Activity timeout: 30 seconds
    Retries: 2
    """
    try:
        logger.info(
            "response_caching_started",
            query=query[:50],
            tokens_used=tokens_used,
        )
        
        success = await response_cache_service.cache_response(
            query=query,
            response=response,
            intent=intent,
            sources=sources,
            tokens_used=tokens_used,
            user_id=UUID(user_id) if user_id else None,
            conversation_id=UUID(conversation_id) if conversation_id else None,
        )
        
        if success:
            logger.info(
                "response_cached_successfully",
                query=query[:50],
            )
        else:
            logger.warning(
                "response_caching_failed",
                query=query[:50],
            )
        
        return success
        
    except Exception as e:
        logger.error(
            "response_caching_error",
            query=query[:50],
            error=str(e),
        )
        # Don't fail workflow on cache errors
        return False


# ============================================================================
# WORKFLOW
# ============================================================================

@workflow.defn(name="ChatWorkflow")
class ChatWorkflow:
    """
    Main chat processing workflow.
    
    Orchestrates:
    1. Cache check
    2. Intent classification
    3. Context retrieval (if needed)
    4. Response generation
    5. Response caching
    
    Duration: 1-5 minutes typical
    Timeout: 10 minutes max
    """
    
    @workflow.run
    async def run(self, input: ChatWorkflowInput) -> ChatWorkflowResult:
        """
        Execute chat workflow.
        
        Args:
            input: Workflow input with message and parameters
            
        Returns:
            Workflow result with response and metadata
        """
        workflow_id = workflow.info().workflow_id
        
        logger.info(
            "chat_workflow_started",
            workflow_id=workflow_id,
            message=input.message[:50],
            user_id=input.user_id,
        )
        
        # Step 1: Check cache (fast path)
        cached_result = await workflow.execute_activity(
            check_response_cache_activity,
            args=[input.message, input.user_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=1),
            ),
        )
        
        if cached_result and input.enable_caching:
            logger.info(
                "workflow_completed_from_cache",
                workflow_id=workflow_id,
            )
            return ChatWorkflowResult(
                response=cached_result["response"],
                intent=cached_result["intent"],
                sources=cached_result["sources"],
                tokens_used=0,  # No tokens used from cache
                model_used="cached",
                from_cache=True,
                workflow_id=workflow_id,
            )
        
        # Step 2: Classify intent
        intent_result = await workflow.execute_activity(
            classify_intent_activity,
            args=[input.message, input.user_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=10),
            ),
        )
        
        # Step 3: Retrieve context (conditional)
        retrieval_result = None
        if intent_result.requires_rag:
            retrieval_result = await workflow.execute_activity(
                retrieve_context_activity,
                args=[input.message, input.user_id, intent_result.primary_intent],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=2),
                ),
            )
        
        # Step 4: Generate response
        generation_result = await workflow.execute_activity(
            generate_response_activity,
            args=[
                input.message,
                retrieval_result.context if retrieval_result else "",
                intent_result.primary_intent,
                input.user_id,
                input.conversation_id,
                input.model,
                input.temperature,
                input.max_tokens,
            ],
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=30),
            ),
        )
        
        # Step 5: Cache response (fire-and-forget)
        if input.enable_caching:
            await workflow.execute_activity(
                cache_response_activity,
                args=[
                    input.message,
                    generation_result.response,
                    intent_result.primary_intent,
                    retrieval_result.sources if retrieval_result else [],
                    generation_result.tokens_used,
                    input.user_id,
                    input.conversation_id,
                ],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=1),
                ),
            )
        
        logger.info(
            "chat_workflow_completed",
            workflow_id=workflow_id,
            intent=intent_result.primary_intent,
            tokens_used=generation_result.tokens_used,
        )
        
        return ChatWorkflowResult(
            response=generation_result.response,
            intent=intent_result.primary_intent,
            sources=retrieval_result.sources if retrieval_result else [],
            tokens_used=generation_result.tokens_used,
            model_used=generation_result.model_used,
            from_cache=generation_result.cache_hit,
            workflow_id=workflow_id,
        )


# Export activities for worker registration
chat_activities = [
    check_response_cache_activity,
    classify_intent_activity,
    retrieve_context_activity,
    generate_response_activity,
    cache_response_activity,
]
