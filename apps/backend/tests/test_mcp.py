"""
Unit tests for Second Brain Model Context Protocol (MCP) Server.
Validates tools/list, tools/call, ADK adapter, and SSE endpoint integration.
"""

import pytest
from app.mcp_server import mcp_server, create_mcp_sse_app
from app.agent import adapt_mcp_tool
from app.main import app
from starlette.testclient import TestClient


@pytest.mark.asyncio
async def test_mcp_tools_list():
    """Validasi bahwa seluruh tools standar MCP terdaftar dengan skema yang benar."""
    tools = await mcp_server.list_tools()
    tool_names = [t.name for t in tools]

    expected_tools = [
        "save_note",
        "search_notes",
        "get_thesis_progress",
        "log_habit",
        "add_task",
        "get_system_telemetry",
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Tool '{expected}' wajib terdaftar di MCP Server"

    # Verifikasi metadata tool
    telemetry_tool = next(t for t in tools if t.name == "get_system_telemetry")
    assert "telemetri" in telemetry_tool.description.lower() or "polyglot" in telemetry_tool.description.lower()


@pytest.mark.asyncio
async def test_mcp_call_system_telemetry():
    """Validasi pemanggilan tools/call untuk 'get_system_telemetry'."""
    result = await mcp_server.call_tool("get_system_telemetry", {})
    assert not result.is_error, "Pemanggilan get_system_telemetry tidak boleh error"

    data = result.structured_content
    assert data is not None, "Response harus menyertakan structured_content"
    assert data["cluster_health"] == "healthy"
    assert data["worker_go"]["port"] == 8085
    assert data["ai_engine"]["port"] == 8000
    assert len(data["git_pipeline"]["repositories"]) == 3


@pytest.mark.asyncio
async def test_mcp_call_thesis_progress():
    """Validasi pemanggilan tools/call untuk 'get_thesis_progress'."""
    result = await mcp_server.call_tool("get_thesis_progress", {})
    assert not result.is_error

    data = result.structured_content
    assert data is not None
    assert "chapters" in data
    assert len(data["chapters"]) >= 5
    assert any("CatBoost" in str(c.get("title", "")) or c.get("chapter_num") == 4 for c in data["chapters"])


@pytest.mark.asyncio
async def test_adk_mcp_tool_adapter():
    """Validasi adapter Google ADK untuk mengonsumsi tool dari MCP server."""
    adk_callable = adapt_mcp_tool("get_system_telemetry")
    assert callable(adk_callable)
    assert adk_callable.__name__ == "get_system_telemetry"

    # Panggil adapter
    output = await adk_callable()
    assert isinstance(output, dict)
    assert output["cluster_health"] == "healthy"


def test_mcp_sse_endpoint_exists():
    """Validasi bahwa endpoint /mcp ter-mount di FastAPI dan siap melayani transport SSE."""
    routes = [r.path for r in app.routes]
    assert any("/mcp" in r for r in routes), "Endpoint /mcp harus ter-mount di aplikasi FastAPI"

    # Verifikasi Starlette app instance
    sse_app = create_mcp_sse_app()
    assert sse_app is not None
    sub_routes = [r.path for r in sse_app.routes]
    assert "/sse" in sub_routes
    assert "/messages" in sub_routes or "/messages/" in sub_routes
