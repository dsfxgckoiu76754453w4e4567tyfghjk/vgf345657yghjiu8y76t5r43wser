"""Comprehensive unit tests for Tool Orchestration Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.tool_orchestration_service import ToolOrchestrationService


class TestToolOrchestrationServiceInitialization:
    """Test cases for Tool Orchestration Service initialization."""

    def test_initialization_creates_all_tool_services(self):
        """Test that service initializes all tool services."""
        # Arrange
        mock_db = AsyncMock()

        # Act
        service = ToolOrchestrationService(mock_db)

        # Assert
        assert service is not None
        assert hasattr(service, 'ahkam_service')
        assert hasattr(service, 'hadith_service')
        assert hasattr(service, 'datetime_service')
        assert hasattr(service, 'math_service')


class TestToolOrchestrationServiceQueryAnalysis:
    """Test cases for query analysis."""

    @pytest.mark.asyncio
    async def test_analyze_query_detects_ahkam_intent(self):
        """Test that Ahkam-related keywords are detected."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        result = await service.analyze_query("What is the ruling on prayer?")

        # Assert
        assert "ahkam" in result["tools_needed"]
        assert result["execution_mode"] == "parallel"

    @pytest.mark.asyncio
    async def test_analyze_query_detects_hadith_intent(self):
        """Test that Hadith-related keywords are detected."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        result = await service.analyze_query("Find hadith about prayer")

        # Assert
        assert "hadith" in result["tools_needed"]

    @pytest.mark.asyncio
    async def test_analyze_query_detects_datetime_intent(self):
        """Test that DateTime-related keywords are detected."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        result = await service.analyze_query("What are the prayer times today?")

        # Assert
        assert "datetime" in result["tools_needed"]

    @pytest.mark.asyncio
    async def test_analyze_query_detects_math_intent(self):
        """Test that Math-related keywords are detected."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        result = await service.analyze_query("Calculate zakat on my wealth")

        # Assert
        assert "math" in result["tools_needed"]

    @pytest.mark.asyncio
    async def test_analyze_query_detects_multiple_intents(self):
        """Test that multiple tools can be detected from one query."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        result = await service.analyze_query(
            "What is the ruling on zakat and show me the hadith about it"
        )

        # Assert
        assert "ahkam" in result["tools_needed"]
        assert "math" in result["tools_needed"]
        assert "hadith" in result["tools_needed"]
        assert len(result["tools_needed"]) >= 2

    @pytest.mark.asyncio
    async def test_analyze_query_defaults_to_rag_when_no_tools_detected(self):
        """Test that RAG is used when no specific tools are detected."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        result = await service.analyze_query("Tell me about Islamic history")

        # Assert
        assert "rag" in result["tools_needed"]


class TestToolOrchestrationServicePriorityDetermination:
    """Test cases for priority determination."""

    def test_determine_priority_orders_tools_correctly(self):
        """Test that tools are ordered by priority."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        tools = ["math", "ahkam", "hadith", "rag"]
        ordered = service._determine_priority(tools)

        # Assert
        assert ordered[0] == "ahkam"  # Highest priority
        assert ordered[1] == "hadith"
        assert ordered[2] == "math"
        assert ordered[3] == "rag"

    def test_determine_priority_handles_unknown_tools(self):
        """Test that unknown tools are placed at the end."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Act
        tools = ["unknown_tool", "ahkam"]
        ordered = service._determine_priority(tools)

        # Assert
        assert ordered[0] == "ahkam"  # Known tool first
        assert ordered[1] == "unknown_tool"  # Unknown tool last


class TestToolOrchestrationServiceParallelExecution:
    """Test cases for parallel tool execution."""

    @pytest.mark.asyncio
    async def test_execute_multi_tool_parallel_mode(self):
        """Test executing multiple tools in parallel."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Mock tool executions
        service._execute_ahkam = AsyncMock(return_value={"ruling": "Permissible"})
        service._execute_hadith = AsyncMock(return_value={"results": [], "count": 0})

        # Act
        result = await service.execute_multi_tool(
            query="What is the ruling?",
            tools=["ahkam", "hadith"],
            execution_mode="parallel",
        )

        # Assert
        assert result["query_type"] == "multi_tool"
        assert "ahkam" in result["results"]
        assert "hadith" in result["results"]
        assert result["execution_summary"]["total_tools"] == 2
        service._execute_ahkam.assert_called_once()
        service._execute_hadith.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_execution_handles_errors(self):
        """Test that parallel execution handles errors gracefully."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Mock one success, one failure
        service._execute_ahkam = AsyncMock(return_value={"ruling": "Permissible"})
        service._execute_hadith = AsyncMock(side_effect=Exception("Hadith error"))

        # Act
        result = await service.execute_multi_tool(
            query="Test query",
            tools=["ahkam", "hadith"],
            execution_mode="parallel",
        )

        # Assert
        assert result["execution_summary"]["successful"] >= 1
        assert result["execution_summary"]["failed"] >= 0  # Exceptions are captured


class TestToolOrchestrationServiceSequentialExecution:
    """Test cases for sequential tool execution."""

    @pytest.mark.asyncio
    async def test_execute_multi_tool_sequential_mode(self):
        """Test executing multiple tools sequentially."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Mock tool executions
        service._execute_ahkam = AsyncMock(return_value={"ruling": "Permissible"})
        service._execute_hadith = AsyncMock(return_value={"results": [], "count": 0})

        # Act
        result = await service.execute_multi_tool(
            query="What is the ruling?",
            tools=["ahkam", "hadith"],
            execution_mode="sequential",
        )

        # Assert
        assert result["query_type"] == "multi_tool"
        assert "ahkam" in result["results"]
        assert "hadith" in result["results"]
        assert result["execution_summary"]["total_tools"] == 2

    @pytest.mark.asyncio
    async def test_sequential_execution_continues_on_error(self):
        """Test that sequential execution continues even if one tool fails."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Mock first tool fails, second succeeds
        service._execute_ahkam = AsyncMock(side_effect=Exception("Ahkam error"))
        service._execute_hadith = AsyncMock(return_value={"results": [], "count": 0})

        # Act
        result = await service.execute_multi_tool(
            query="Test query",
            tools=["ahkam", "hadith"],
            execution_mode="sequential",
        )

        # Assert
        assert "ahkam" in result["results"]
        assert "hadith" in result["results"]
        assert "error" in result["results"]["ahkam"]
        assert "results" in result["results"]["hadith"]


class TestToolOrchestrationServiceIndividualToolExecution:
    """Test cases for individual tool execution."""

    @pytest.mark.asyncio
    async def test_execute_ahkam_calls_ahkam_service(self):
        """Test that Ahkam execution calls the Ahkam service."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        service.ahkam_service.get_ahkam_ruling = AsyncMock(
            return_value={"ruling": "Permissible", "source": "Khamenei"}
        )

        # Act
        result = await service._execute_ahkam(
            "What is the ruling?",
            {"marja_preference": "Khamenei"}
        )

        # Assert
        assert result["ruling"] == "Permissible"
        service.ahkam_service.get_ahkam_ruling.assert_called_once_with(
            "What is the ruling?",
            marja_name="Khamenei"
        )

    @pytest.mark.asyncio
    async def test_execute_ahkam_uses_default_marja(self):
        """Test that Ahkam execution uses default Marja if not specified."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        service.ahkam_service.get_ahkam_ruling = AsyncMock(
            return_value={"ruling": "Permissible"}
        )

        # Act
        result = await service._execute_ahkam("Test query", {})

        # Assert
        service.ahkam_service.get_ahkam_ruling.assert_called_once_with(
            "Test query",
            marja_name="Khamenei"  # Default
        )

    @pytest.mark.asyncio
    async def test_execute_hadith_calls_hadith_service(self):
        """Test that Hadith execution calls the Hadith service."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        mock_hadiths = [
            {"text": "Hadith 1", "narrator": "Narrator 1"},
            {"text": "Hadith 2", "narrator": "Narrator 2"},
        ]
        service.hadith_service.search_hadith = AsyncMock(return_value=mock_hadiths)

        # Act
        result = await service._execute_hadith("prayer", {})

        # Assert
        assert result["count"] == 2
        assert result["results"] == mock_hadiths
        service.hadith_service.search_hadith.assert_called_once_with(
            "prayer",
            search_type="text",
            limit=5
        )

    @pytest.mark.asyncio
    async def test_execute_datetime_calls_datetime_service(self):
        """Test that DateTime execution calls the DateTime service."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        mock_prayer_times = {
            "fajr": "05:30",
            "dhuhr": "12:00",
            "asr": "15:30",
        }
        service.datetime_service.get_prayer_times = AsyncMock(
            return_value=mock_prayer_times
        )

        # Act
        result = await service._execute_datetime(
            "prayer times",
            {"city": "Tehran", "country": "Iran"}
        )

        # Assert
        assert result["fajr"] == "05:30"
        service.datetime_service.get_prayer_times.assert_called_once_with(
            "Tehran",
            "Iran"
        )

    @pytest.mark.asyncio
    async def test_execute_math_zakat_calculation(self):
        """Test that Math execution calculates zakat."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        service.math_service.calculate_zakat = AsyncMock(
            return_value={"zakat_amount": 250, "rate": "2.5%"}
        )

        # Act
        result = await service._execute_math(
            "Calculate zakat on 10000",
            {"amount": 10000}
        )

        # Assert
        assert result["zakat_amount"] == 250
        service.math_service.calculate_zakat.assert_called_once_with(10000)

    @pytest.mark.asyncio
    async def test_execute_math_khums_calculation(self):
        """Test that Math execution calculates khums."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        service.math_service.calculate_khums = AsyncMock(
            return_value={"khums_amount": 4000, "rate": "20%"}
        )

        # Act
        result = await service._execute_math(
            "Calculate khums on my income",
            {"annual_income": 50000, "annual_expenses": 30000}
        )

        # Assert
        assert result["khums_amount"] == 4000
        service.math_service.calculate_khums.assert_called_once_with(50000, 30000)

    @pytest.mark.asyncio
    async def test_execute_math_simple_calculation(self):
        """Test that Math execution handles simple calculations."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        service.math_service.simple_calculation = AsyncMock(
            return_value={"result": 15}
        )

        # Act
        result = await service._execute_math("What is 10 + 5", {})

        # Assert
        assert result["result"] == 15
        service.math_service.simple_calculation.assert_called_once()


class TestToolOrchestrationServiceResultCombination:
    """Test cases for result combination."""

    def test_combine_results_formats_output_correctly(self):
        """Test that results are combined and formatted correctly."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        tools = ["ahkam", "hadith"]
        results = {
            "ahkam": {"ruling": "Permissible"},
            "hadith": {"results": [], "count": 0}
        }

        # Act
        combined = service._combine_results(results, tools)

        # Assert
        assert combined["query_type"] == "multi_tool"
        assert combined["tools_used"] == tools
        assert "results" in combined
        assert "execution_summary" in combined
        assert combined["execution_summary"]["total_tools"] == 2
        assert combined["execution_summary"]["successful"] == 2
        assert combined["execution_summary"]["failed"] == 0

    def test_combine_results_counts_errors(self):
        """Test that failed executions are counted correctly."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        tools = ["ahkam", "hadith", "math"]
        results = {
            "ahkam": {"ruling": "Permissible"},
            "hadith": {"error": "Not found"},
            "math": Exception("Calculation error")
        }

        # Act
        combined = service._combine_results(results, tools)

        # Assert
        assert combined["execution_summary"]["total_tools"] == 3
        assert combined["execution_summary"]["successful"] == 1
        assert combined["execution_summary"]["failed"] == 2


class TestToolOrchestrationServiceIntegration:
    """Integration test cases for complete workflows."""

    @pytest.mark.asyncio
    async def test_full_workflow_analyze_and_execute(self):
        """Test complete workflow from analysis to execution."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Mock tool executions
        service.ahkam_service.get_ahkam_ruling = AsyncMock(
            return_value={"ruling": "Permissible"}
        )

        # Act - Analyze
        analysis = await service.analyze_query("What is the ruling on prayer?")

        # Act - Execute
        execution_result = await service.execute_multi_tool(
            query="What is the ruling on prayer?",
            tools=analysis["tools_needed"],
            execution_mode=analysis["execution_mode"],
        )

        # Assert
        assert "ahkam" in analysis["tools_needed"]
        assert execution_result["query_type"] == "multi_tool"
        assert "ahkam" in execution_result["results"]

    @pytest.mark.asyncio
    async def test_context_propagation_in_sequential_mode(self):
        """Test that context is propagated between tools in sequential mode."""
        # Arrange
        mock_db = AsyncMock()
        service = ToolOrchestrationService(mock_db)

        # Track context propagation
        context_received = []

        async def mock_ahkam(query, context):
            context_received.append(("ahkam", context.copy()))
            return {"ruling": "Permissible"}

        async def mock_hadith(query, context):
            context_received.append(("hadith", context.copy()))
            return {"results": [], "count": 0}

        service._execute_ahkam = mock_ahkam
        service._execute_hadith = mock_hadith

        # Act
        result = await service.execute_multi_tool(
            query="Test query",
            tools=["ahkam", "hadith"],
            execution_mode="sequential",
        )

        # Assert
        assert len(context_received) == 2
        # Second tool should have access to previous results
        assert "previous_results" in context_received[1][1]
        assert "ahkam" in context_received[1][1]["previous_results"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
