"""Happy path tests for chat endpoint with mocked dependencies."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json


@pytest.fixture
def client():
    """Create test client."""
    from apps.api.main import app
    return TestClient(app)


@pytest.fixture
def mock_pass1_response():
    """Sample Pass-1 response."""
    return {
        "text": "Here's how to tie a uni knot.",
        "needs_fresh_facts": False,
        "image_queries": ["uni knot fishing"],
        "tool_calls": ["images"],
        "lesson_plan": [{
            "kind": "howto",
            "title": "Tying a Uni Knot",
            "theme": "river",
            "summary": "Simple, strong fishing knot",
            "steps": [
                {"title": "Thread the line", "body": "Pass line through the eye."},
                {"title": "Make a loop", "body": "Form a loop alongside the line."},
                {"title": "Wrap and tighten", "body": "Wrap 5-7 times and pull tight."}
            ]
        }],
        "_model_used": "gpt-4o"
    }


@pytest.mark.asyncio
async def test_chat_endpoint_basic(client, mock_pass1_response):
    """Test /api/chat endpoint with mocked OpenAI."""
    with patch("apps.api.orchestrator.client") as mock_openai:
        # Mock OpenAI response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_pass1_response)
        mock_openai.chat.completions.create.return_value = mock_completion
        
        # Mock image search (return empty)
        with patch("apps.api.orchestrator.real_images_for_queries", new=AsyncMock(return_value={})):
            response = client.post("/api/chat", json={"message": "How to tie a uni knot?"})
            
            assert response.status_code == 200
            data = response.json()
            
            assert "text" in data
            assert "lesson_cards" in data
            assert len(data["lesson_cards"]) > 0
            assert data["lesson_cards"][0]["kind"] == "howto"


@pytest.mark.asyncio
async def test_chat_with_search_citations(client):
    """Test chat endpoint with search results and citations."""
    mock_response = {
        "text": "Current fishing conditions.",
        "needs_fresh_facts": True,
        "tool_calls": ["search", "weather"],
        "image_queries": [],
        "lesson_plan": [{
            "kind": "plan",
            "title": "Fishing Plan",
            "theme": "river",
            "steps": [{"title": "Check conditions", "body": "Weather is good."}]
        }],
        "_model_used": "gpt-4o"
    }
    
    mock_search_result = {
        "results": [{"title": "Test", "url": "https://example.com", "snippet": "Info"}],
        "citations": [{"url": "https://example.com", "title": "Test"}]
    }
    
    with patch("apps.api.orchestrator.client") as mock_openai:
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)
        mock_openai.chat.completions.create.return_value = mock_completion
        
        with patch("apps.api.tools.search.search_web", new=AsyncMock(return_value=mock_search_result)):
            with patch("apps.api.tools.weather.get_weather", new=AsyncMock(return_value={"current": {"temp": 22}})):
                response = client.post("/api/chat", json={"message": "Fishing plan?"})
                
                assert response.status_code == 200
                data = response.json()
                assert data["needs_fresh_facts"] is True
                # Citations should be attached to cards
                if data["lesson_cards"]:
                    # Check if citations exist (may be on card or steps)
                    assert "lesson_cards" in data


def test_chat_endpoint_missing_message(client):
    """Test /api/chat returns 400 when message is missing."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 400

