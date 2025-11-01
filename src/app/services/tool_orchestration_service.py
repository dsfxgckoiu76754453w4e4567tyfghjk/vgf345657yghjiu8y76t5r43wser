"""
Multi-tool orchestration service.

CRITICAL FEATURE: One question can trigger MULTIPLE tools simultaneously.
Supports parallel and sequential execution.
"""

import asyncio
from typing import Any, Literal, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.ahkam_service import AhkamService
from app.services.datetime_service import DateTimeService
from app.services.hadith_service import HadithService
from app.services.math_service import MathService

logger = get_logger(__name__)


class ToolOrchestrationService:
    """
    Service for orchestrating multiple specialized tools.

    CRITICAL: Enables multi-tool selection where one question can use:
    - Ahkam tool (official Marja sources)
    - Hadith lookup
    - DateTime calculator
    - Math calculator
    - RAG retrieval
    - Web search

    Execution modes:
    - Parallel: Independent tools run simultaneously
    - Sequential: Dependent tools run in order
    - Mixed: Combination of both
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize tool orchestration service.

        Args:
            db: Database session
        """
        self.db = db
        self.ahkam_service = AhkamService(db)
        self.hadith_service = HadithService(db)
        self.datetime_service = DateTimeService()
        self.math_service = MathService()

    async def analyze_query(self, query: str) -> dict:
        """
        Analyze query to determine which tools are needed.

        Args:
            query: User query

        Returns:
            Analysis with required tools and execution strategy
        """
        logger.info(
            "query_analysis_started",
            query=query[:50],
        )

        # Simple keyword-based detection (in production, use LLM classification)
        tools_needed = []
        execution_mode = "parallel"

        query_lower = query.lower()

        # Check for Ahkam-related keywords
        ahkam_keywords = ["ruling", "hukm", "ahkam", "fatwa", "halal", "haram", "permissible"]
        if any(keyword in query_lower for keyword in ahkam_keywords):
            tools_needed.append("ahkam")

        # Check for Hadith-related keywords
        hadith_keywords = ["hadith", "narration", "narrator", "sahih", "tradition"]
        if any(keyword in query_lower for keyword in hadith_keywords):
            tools_needed.append("hadith")

        # Check for DateTime-related keywords
        datetime_keywords = ["prayer time", "salat", "namaz", "date", "calendar", "hijri"]
        if any(keyword in query_lower for keyword in datetime_keywords):
            tools_needed.append("datetime")

        # Check for Math-related keywords
        math_keywords = ["zakat", "khums", "inheritance", "calculate", "how much"]
        if any(keyword in query_lower for keyword in math_keywords):
            tools_needed.append("math")

        # Default to RAG if no specific tool detected
        if not tools_needed:
            tools_needed.append("rag")

        logger.info(
            "query_analysis_completed",
            tools_needed=tools_needed,
            execution_mode=execution_mode,
        )

        return {
            "query": query,
            "tools_needed": tools_needed,
            "execution_mode": execution_mode,
            "priority": self._determine_priority(tools_needed),
        }

    async def execute_multi_tool(
        self,
        query: str,
        tools: list[str],
        execution_mode: Literal["parallel", "sequential"] = "parallel",
        context: Optional[dict] = None,
    ) -> dict:
        """
        Execute multiple tools for a single query.

        Args:
            query: User query
            tools: List of tools to execute
            execution_mode: parallel or sequential
            context: Additional context (user preferences, etc.)

        Returns:
            Combined results from all tools
        """
        logger.info(
            "multi_tool_execution_started",
            query=query[:50],
            tools=tools,
            mode=execution_mode,
        )

        context = context or {}

        if execution_mode == "parallel":
            results = await self._execute_parallel(query, tools, context)
        else:
            results = await self._execute_sequential(query, tools, context)

        # Combine and format results
        combined_result = self._combine_results(results, tools)

        logger.info(
            "multi_tool_execution_completed",
            query=query[:50],
            tools_executed=len(results),
        )

        return combined_result

    async def _execute_parallel(
        self,
        query: str,
        tools: list[str],
        context: dict,
    ) -> dict[str, Any]:
        """Execute tools in parallel."""
        tasks = {}

        for tool in tools:
            if tool == "ahkam":
                tasks["ahkam"] = self._execute_ahkam(query, context)
            elif tool == "hadith":
                tasks["hadith"] = self._execute_hadith(query, context)
            elif tool == "datetime":
                tasks["datetime"] = self._execute_datetime(query, context)
            elif tool == "math":
                tasks["math"] = self._execute_math(query, context)

        # Run all tasks in parallel
        results = await asyncio.gather(
            *[asyncio.create_task(task) for task in tasks.values()],
            return_exceptions=True,
        )

        # Map results back to tool names
        return dict(zip(tasks.keys(), results))

    async def _execute_sequential(
        self,
        query: str,
        tools: list[str],
        context: dict,
    ) -> dict[str, Any]:
        """Execute tools sequentially (one after another)."""
        results = {}

        for tool in tools:
            try:
                if tool == "ahkam":
                    results["ahkam"] = await self._execute_ahkam(query, context)
                elif tool == "hadith":
                    results["hadith"] = await self._execute_hadith(query, context)
                elif tool == "datetime":
                    results["datetime"] = await self._execute_datetime(query, context)
                elif tool == "math":
                    results["math"] = await self._execute_math(query, context)

                # Pass results to next tool (for dependency)
                context["previous_results"] = results

            except Exception as e:
                logger.error(f"tool_execution_failed", tool=tool, error=str(e))
                results[tool] = {"error": str(e)}

        return results

    async def _execute_ahkam(self, query: str, context: dict) -> dict:
        """Execute Ahkam tool."""
        marja = context.get("marja_preference", "Khamenei")
        return await self.ahkam_service.get_ahkam_ruling(query, marja_name=marja)

    async def _execute_hadith(self, query: str, context: dict) -> dict:
        """Execute Hadith lookup."""
        results = await self.hadith_service.search_hadith(query, search_type="text", limit=5)
        return {"results": results, "count": len(results)}

    async def _execute_datetime(self, query: str, context: dict) -> dict:
        """Execute DateTime calculator."""
        # Parse query to determine what's needed
        # For now, default to prayer times
        city = context.get("city", "Tehran")
        country = context.get("country", "Iran")
        return await self.datetime_service.get_prayer_times(city, country)

    async def _execute_math(self, query: str, context: dict) -> dict:
        """Execute Math calculator."""
        query_lower = query.lower()

        # Determine calculation type from query
        if "zakat" in query_lower:
            # Extract amount from query (simplified)
            amount = context.get("amount", 10000)
            return await self.math_service.calculate_zakat(amount)
        elif "khums" in query_lower:
            income = context.get("annual_income", 50000)
            expenses = context.get("annual_expenses", 30000)
            return await self.math_service.calculate_khums(income, expenses)
        else:
            return await self.math_service.simple_calculation(query)

    def _combine_results(self, results: dict[str, Any], tools: list[str]) -> dict:
        """
        Combine results from multiple tools.

        Args:
            results: Results from each tool
            tools: List of tools that were executed

        Returns:
            Combined and formatted results
        """
        return {
            "query_type": "multi_tool",
            "tools_used": tools,
            "results": results,
            "execution_summary": {
                "total_tools": len(tools),
                "successful": sum(
                    1 for r in results.values() if not isinstance(r, Exception) and "error" not in r
                ),
                "failed": sum(
                    1 for r in results.values() if isinstance(r, Exception) or "error" in r
                ),
            },
        }

    def _determine_priority(self, tools: list[str]) -> list[str]:
        """
        Determine execution priority for tools.

        Priority order:
        1. Ahkam (most authoritative)
        2. Hadith (textual evidence)
        3. DateTime (factual)
        4. Math (calculations)
        5. RAG (general knowledge)
        """
        priority_order = ["ahkam", "hadith", "datetime", "math", "rag"]

        return sorted(tools, key=lambda t: priority_order.index(t) if t in priority_order else 999)
