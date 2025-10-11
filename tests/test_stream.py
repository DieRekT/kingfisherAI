"""Tests for SSE streaming endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json


@pytest.fixture
def client():
    """Create test client."""
    from apps.api.main import app
    return TestClient(app)


def test_stream_endpoint_missing_message(client):
    """Test /api/chat/stream returns 400 when message is missing."""
    response = client.get("/api/chat/stream")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_stream_endpoint_events(client):
    """Test /api/chat/stream emits correct SSE events."""
    mock_response = {
        "text": "Test response",
        "needs_fresh_facts": False,
        "tool_calls": [],
        "image_queries": [],
        "lesson_plan": [{
            "kind": "concept",
            "title": "Test Card",
            "theme": "river",
            "steps": [{"title": "Step 1", "body": "Body 1"}]
        }],
        "_model_used": "gpt-4o"
    }
    
    with patch("apps.api.orchestrator.client") as mock_openai:
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)
        mock_openai.chat.completions.create.return_value = mock_completion
        
        with patch("apps.api.orchestrator.real_images_for_queries", new=AsyncMock(return_value={})):
            response = client.get("/api/chat/stream?message=test")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Parse SSE events
            events = []
            for line in response.iter_lines():
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix
                    try:
                        events.append(json.loads(data_str))
                    except:
                        pass
            
            # Check we got some events
            assert len(events) > 0
            
            # First event should be status
            assert events[0]["type"] == "status"
            assert events[0]["stage"] == "planning"
            
            # Last event should be result
            assert events[-1]["type"] == "result"
            assert "payload" in events[-1]

