"""LangGraph orchestration service for RAG workflows."""

import json
from typing import Any, Annotated, TypedDict
from operator import add
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.services.intent_detector import IntentDetector, IntentType
from app.services.document_service import DocumentService

logger = get_logger(__name__)


# Define state for the RAG graph
class RAGState(TypedDict):
    """State for RAG processing graph."""

    # Input
    query: str
    user_id: str
    conversation_id: str

    # Processing
    intent: str  # classification: general_qa, ahkam, hadith, complex
    requires_rag: bool
    requires_tools: list[str]

    # RAG components
    retrieved_chunks: list[dict[str, Any]]
    context: str

    # Output
    response: str
    sources: list[dict[str, Any]]
    tokens_used: int

    # Messages for LLM
    messages: Annotated[list, add]


class LangGraphService:
    """
    LangGraph-based orchestration for RAG workflows.

    Handles:
    - Intent classification via IntentDetector
    - RAG retrieval via DocumentService
    - Tool selection
    - Response generation
    """

    def __init__(self, db: AsyncSession | None = None):
        """
        Initialize LangGraph service.

        Args:
            db: Database session for document retrieval
        """
        self.db = db
        self.llm = self._get_llm()
        self.intent_detector = IntentDetector()
        self.graph = self._build_graph()

    def _get_llm(self):
        """Get LLM based on configuration."""
        if settings.llm_provider == "openrouter":
            # OpenRouter uses OpenAI-compatible API
            if not settings.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")

            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": settings.openrouter_app_url,
                    "X-Title": settings.openrouter_app_name,
                },
            )

        elif settings.llm_provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openai_api_key,
            )

        elif settings.llm_provider == "google":
            if not settings.google_api_key:
                raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=google")

            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.google_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}. Use 'openrouter' (recommended), 'openai', or 'google'. For Claude models, use 'openrouter' with model='anthropic/claude-3.5-sonnet'.")

    def _build_graph(self) -> StateGraph:
        """
        Build the RAG processing graph.

        Graph flow:
        1. classify_intent -> Determine query type using IntentDetector
        2. retrieve (if needed) -> Get relevant chunks from DocumentService
        3. generate -> Generate response using LLM with context
        """
        workflow = StateGraph(RAGState)

        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("retrieve", self._retrieve_chunks)
        workflow.add_node("generate", self._generate_response)

        # Define edges
        workflow.set_entry_point("classify_intent")

        # Conditional routing after classification
        workflow.add_conditional_edges(
            "classify_intent",
            self._should_retrieve,
            {
                True: "retrieve",
                False: "generate",
            },
        )

        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    async def _classify_intent(self, state: RAGState) -> RAGState:
        """
        Classify the user's intent using IntentDetector.

        Determines:
        - Query type (image_generation, web_search, document_search, etc.)
        - Whether RAG retrieval is needed
        - Which tools might be needed
        """
        query = state["query"]

        # Use IntentDetector for multi-intent detection
        detected_intents = await self.intent_detector.detect_intents(
            message=query,
            language="auto"  # Auto-detect language (en, fa, ar)
        )

        # Determine primary intent
        primary_intent = "question_answer"  # Default
        requires_rag = False
        requires_tools = []

        if detected_intents:
            # Get highest priority intent
            primary = detected_intents[0]
            primary_intent = primary.intent_type.value

            # Check if document search is needed (RAG)
            if any(i.intent_type == IntentType.DOCUMENT_SEARCH for i in detected_intents):
                requires_rag = True
                requires_tools.append("document_search")

            # Check for other intents
            for intent in detected_intents:
                if intent.intent_type == IntentType.IMAGE_GENERATION:
                    requires_tools.append("image_generation")
                elif intent.intent_type in [IntentType.WEB_SEARCH, IntentType.DEEP_WEB_SEARCH]:
                    requires_tools.append("web_search")
                elif intent.intent_type == IntentType.TOOL_USAGE:
                    requires_tools.append("tools")

        # For Islamic Q&A, we always want RAG (knowledge base retrieval)
        if primary_intent == "question_answer" and not requires_tools:
            requires_rag = True

        logger.info(
            "intent_classified",
            query=query[:50],
            primary_intent=primary_intent,
            requires_rag=requires_rag,
            tools_needed=requires_tools,
            detected_intents_count=len(detected_intents),
        )

        return {
            **state,
            "intent": primary_intent,
            "requires_rag": requires_rag,
            "requires_tools": requires_tools,
            "messages": [],
        }

    async def _retrieve_chunks(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant chunks from vector DB using DocumentService.

        Uses semantic search to find the most relevant Islamic knowledge.
        """
        query = state["query"]
        user_id = state["user_id"]

        retrieved_chunks = []
        context = ""

        # Only retrieve if we have a database session
        if self.db:
            try:
                # Use DocumentService for semantic search
                doc_service = DocumentService(self.db)

                # Search for relevant chunks (top 5)
                chunks = await doc_service.semantic_search(
                    query=query,
                    limit=5,
                    user_id=UUID(user_id) if user_id else None,
                    min_score=0.7,  # Only high-quality matches
                )

                # Format chunks for response
                retrieved_chunks = [
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
                    f"Source: {chunk['source']} (Relevance: {chunk['score']:.2%})\n{chunk['content']}"
                    for chunk in retrieved_chunks
                ])

                logger.info(
                    "chunks_retrieved",
                    query=query[:50],
                    count=len(retrieved_chunks),
                    avg_score=sum(c['score'] for c in retrieved_chunks) / len(retrieved_chunks) if retrieved_chunks else 0,
                )

            except Exception as e:
                logger.error(
                    "chunk_retrieval_failed",
                    query=query[:50],
                    error=str(e),
                )
                # Continue without RAG on failure
                retrieved_chunks = []
                context = ""
        else:
            logger.warning(
                "no_db_session",
                message="Cannot retrieve chunks without database session",
            )

        return {
            **state,
            "retrieved_chunks": retrieved_chunks,
            "context": context,
        }

    async def _generate_response(self, state: RAGState) -> RAGState:
        """
        Generate response using LLM with RAG context.

        Uses retrieved context if available, otherwise generates from LLM knowledge.
        """
        query = state["query"]
        context = state.get("context", "")
        intent = state.get("intent", "question_answer")

        # Build prompt based on whether we have context
        if context:
            system_prompt = f"""You are a knowledgeable Shia Islamic scholar assistant.
Answer the question using the provided context from authenticated Islamic sources.

Context from Islamic knowledge base:
{context}

Guidelines:
- Always cite your sources when using the context
- If the context doesn't contain enough information, you may supplement with your knowledge
- Be respectful and accurate in all Islamic discussions
- Use clear citations like [Source: Book Name]"""
        else:
            system_prompt = """You are a knowledgeable Shia Islamic scholar assistant.
Provide accurate information about Shia Islam based on authenticated sources.

Guidelines:
- Be respectful and accurate in all Islamic discussions
- Cite traditional sources when making Islamic rulings
- If unsure, acknowledge the limits of your knowledge"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]

        # Generate response
        try:
            response = await self.llm.ainvoke(messages)

            # Extract token usage if available
            tokens_used = 0
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('usage', {})
                tokens_used = usage.get('total_tokens', 0)

            logger.info(
                "response_generated",
                query=query[:50],
                has_context=bool(context),
                intent=intent,
                tokens_used=tokens_used,
                response_length=len(response.content),
            )

            return {
                **state,
                "response": response.content,
                "sources": state.get("retrieved_chunks", []),
                "tokens_used": tokens_used,
            }

        except Exception as e:
            logger.error(
                "response_generation_failed",
                query=query[:50],
                error=str(e),
            )

            # Return error message
            return {
                **state,
                "response": "I apologize, but I encountered an error generating the response. Please try again.",
                "sources": [],
                "tokens_used": 0,
            }

    def _should_retrieve(self, state: RAGState) -> bool:
        """Determine if RAG retrieval is needed based on intent classification."""
        return state.get("requires_rag", True)

    async def process_query(
        self,
        query: str,
        user_id: str,
        conversation_id: str,
    ) -> dict[str, Any]:
        """
        Process a query through the RAG graph.

        Args:
            query: User query
            user_id: User ID
            conversation_id: Conversation ID

        Returns:
            Processing result with response and metadata
        """
        logger.info(
            "langgraph_processing_started",
            query=query[:50],
            user_id=user_id,
            conversation_id=conversation_id,
        )

        # Initialize state
        initial_state = RAGState(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            intent="",
            requires_rag=True,
            requires_tools=[],
            retrieved_chunks=[],
            context="",
            response="",
            sources=[],
            tokens_used=0,
            messages=[],
        )

        # Run the graph
        try:
            result = await self.graph.ainvoke(initial_state)

            logger.info(
                "langgraph_processing_completed",
                query=query[:50],
                intent=result.get("intent"),
                sources_count=len(result.get("sources", [])),
                tokens_used=result.get("tokens_used", 0),
            )

            return {
                "response": result.get("response", ""),
                "intent": result.get("intent", ""),
                "sources": result.get("sources", []),
                "tokens_used": result.get("tokens_used", 0),
                "retrieved_chunks": result.get("retrieved_chunks", []),
            }

        except Exception as e:
            logger.error(
                "langgraph_processing_failed",
                query=query[:50],
                error=str(e),
            )

            return {
                "response": "I apologize, but I encountered an error processing your query. Please try again.",
                "intent": "error",
                "sources": [],
                "tokens_used": 0,
                "retrieved_chunks": [],
            }


def get_langgraph_service(db: AsyncSession) -> LangGraphService:
    """
    Factory function to create LangGraphService with database session.

    Args:
        db: Database session for document retrieval

    Returns:
        Configured LangGraphService instance
    """
    return LangGraphService(db=db)
