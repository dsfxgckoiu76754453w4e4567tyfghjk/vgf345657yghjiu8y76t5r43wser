"""LangGraph orchestration service for RAG workflows."""

from typing import Any, Annotated, TypedDict
from operator import add

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.core.logging import get_logger

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
    - Intent classification
    - RAG retrieval
    - Tool selection
    - Response generation
    """

    def __init__(self):
        """Initialize LangGraph service."""
        self.llm = self._get_llm()
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

        elif settings.llm_provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")

            return ChatAnthropic(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.anthropic_api_key,
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    def _build_graph(self) -> StateGraph:
        """
        Build the RAG processing graph.

        Graph flow:
        1. classify_intent -> Determine query type
        2. retrieve (if needed) -> Get relevant chunks
        3. generate -> Generate response
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
        Classify the user's intent.

        Determines:
        - Query type (general_qa, ahkam, hadith, etc.)
        - Whether RAG retrieval is needed
        - Which tools might be needed
        """
        query = state["query"]

        # Simple classification prompt
        classification_prompt = f"""Classify this Islamic question:
Query: {query}

Determine:
1. Intent: general_qa, ahkam, hadith, datetime, math, or complex
2. Requires RAG: true/false (does it need knowledge base retrieval?)

Respond in JSON format:
{{"intent": "...", "requires_rag": true/false, "requires_tools": ["tool1", "tool2"]}}
"""

        messages = [HumanMessage(content=classification_prompt)]
        response = await self.llm.ainvoke(messages)

        # Parse response (simplified - in production use structured output)
        intent = "general_qa"  # Default
        requires_rag = True
        requires_tools = []

        logger.info(
            "intent_classified",
            query=query[:50],
            intent=intent,
            requires_rag=requires_rag,
        )

        return {
            **state,
            "intent": intent,
            "requires_rag": requires_rag,
            "requires_tools": requires_tools,
            "messages": [response],
        }

    async def _retrieve_chunks(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant chunks from vector DB.

        Uses the document service for semantic search.
        """
        query = state["query"]

        # TODO: Integrate with DocumentService
        # For now, return empty
        retrieved_chunks = []
        context = ""

        logger.info(
            "chunks_retrieved",
            query=query[:50],
            count=len(retrieved_chunks),
        )

        return {
            **state,
            "retrieved_chunks": retrieved_chunks,
            "context": context,
        }

    async def _generate_response(self, state: RAGState) -> RAGState:
        """
        Generate response using LLM.

        Uses RAG context if available.
        """
        query = state["query"]
        context = state.get("context", "")

        # Build prompt
        if context:
            system_prompt = f"""You are a knowledgeable Shia Islamic scholar assistant.
Answer the question using the provided context.

Context:
{context}

Always cite your sources when using the context."""
        else:
            system_prompt = """You are a knowledgeable Shia Islamic scholar assistant.
Provide accurate information about Shia Islam."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]

        response = await self.llm.ainvoke(messages)

        logger.info(
            "response_generated",
            query=query[:50],
            has_context=bool(context),
        )

        return {
            **state,
            "response": response.content,
            "sources": [],
            "tokens_used": 0,  # TODO: Calculate from response
        }

    def _should_retrieve(self, state: RAGState) -> bool:
        """Determine if RAG retrieval is needed."""
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
        result = await self.graph.ainvoke(initial_state)

        logger.info(
            "langgraph_processing_completed",
            query=query[:50],
            intent=result.get("intent"),
        )

        return {
            "response": result.get("response", ""),
            "intent": result.get("intent", ""),
            "sources": result.get("sources", []),
            "tokens_used": result.get("tokens_used", 0),
        }


# Global LangGraph service instance
langgraph_service = LangGraphService()
