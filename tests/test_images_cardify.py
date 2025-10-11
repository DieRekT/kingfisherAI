"""Tests for step-visual cardify and image attachment."""
import asyncio
import pytest
from apps.api.orchestrator import _cardify_steps, _attach_step_images, _is_step_visual_task


class DummyHit(dict):
    """Dummy image result for testing."""
    pass


async def fake_unsplash_search(query: str, per_page: int = 1):
    """Fake Unsplash search that returns dummy results."""
    return [DummyHit(
        url="https://example.org/demo.jpg",
        alt=query,
        credit="Photo by Demo on Unsplash",
        href="https://unsplash.com",
        provider="unsplash"
    )]


def test_is_step_visual_task_detects_knots():
    """Test that knot-related prompts are detected as step-visual."""
    plan = {"lesson_plan": []}
    assert _is_step_visual_task("How to tie a uni knot", plan) is True
    assert _is_step_visual_task("teach me fishing knots", plan) is True


def test_is_step_visual_task_detects_rigs():
    """Test that rig-related prompts are detected as step-visual."""
    plan = {"lesson_plan": []}
    assert _is_step_visual_task("how to rig a soft plastic", plan) is True
    assert _is_step_visual_task("Setup a Carolina rig", plan) is True


def test_is_step_visual_task_ignores_general():
    """Test that general prompts are NOT detected as step-visual."""
    plan = {"lesson_plan": []}
    assert _is_step_visual_task("What's the best bait for bream", plan) is False
    assert _is_step_visual_task("Where to fish in Clarence River", plan) is False


def test_cardify_steps_structure():
    """Test that cardify creates overview + per-step cards."""
    plan = {
        "lesson_plan": [{
            "title": "Uni Knot",
            "kind": "howto",
            "theme": "river",
            "summary": "A reliable terminal knot",
            "steps": [
                {"title": "Thread the line", "body": "Pass tag end twice."},
                {"title": "Wrap 5 times", "body": "Around standing line."},
                {"title": "Tighten", "body": "Pull slowly and wet the line."},
            ],
        }]
    }
    out = _cardify_steps(plan)
    titles = [c["title"] for c in out["lesson_plan"]]
    
    # Should have overview + 3 step cards
    assert len(titles) == 4
    assert any("Overview" in t for t in titles), f"Expected overview card in {titles}"
    assert any("Step 1" in t for t in titles), f"Expected Step 1 card in {titles}"
    assert any("Step 2" in t for t in titles), f"Expected Step 2 card in {titles}"
    assert any("Step 3" in t for t in titles), f"Expected Step 3 card in {titles}"


def test_cardify_preserves_single_step_cards():
    """Test that single-step cards are not cardified."""
    plan = {
        "lesson_plan": [{
            "title": "Quick Tip",
            "kind": "howto",
            "theme": "slate",
            "summary": "A single tip",
            "steps": [
                {"title": "Use fluorocarbon", "body": "Better abrasion resistance."},
            ],
        }]
    }
    out = _cardify_steps(plan)
    
    # Should have only 1 card (not split)
    assert len(out["lesson_plan"]) == 1
    assert out["lesson_plan"][0]["title"] == "Quick Tip"


def test_cardify_preserves_non_howto_cards():
    """Test that concept/reference cards are not cardified."""
    plan = {
        "lesson_plan": [{
            "title": "Knot Strength Comparison",
            "kind": "reference",
            "theme": "ocean",
            "summary": "Common knot strengths",
            "steps": [
                {"title": "FG Knot", "body": "95% line strength"},
                {"title": "Uni to Uni", "body": "85% line strength"},
            ],
        }]
    }
    out = _cardify_steps(plan)
    
    # Should have only 1 card (not split)
    assert len(out["lesson_plan"]) == 1
    assert out["lesson_plan"][0]["kind"] == "reference"


@pytest.mark.asyncio
async def test_attach_step_images_with_fake_search(monkeypatch):
    """Test that step images are attached correctly (using fake search)."""
    from apps.api import orchestrator as o
    monkeypatch.setattr(o, "unsplash_search", fake_unsplash_search)
    
    plan = {
        "lesson_plan": [
            {
                "title": "Uni Knot — Overview",
                "kind": "howto",
                "theme": "river",
                "summary": "Overview",
                "steps": [
                    {"title": "Thread", "body": ""},
                    {"title": "Wrap", "body": ""},
                ]
            },
            {
                "title": "Step 1: Thread the line",
                "kind": "howto",
                "theme": "river",
                "summary": "Detailed view of step 1",
                "steps": [{"title": "Thread the line", "body": "Pass tag end twice."}]
            },
            {
                "title": "Step 2: Wrap 5 times",
                "kind": "howto",
                "theme": "river",
                "summary": "Detailed view of step 2",
                "steps": [{"title": "Wrap 5 times", "body": "Around standing line."}]
            },
        ]
    }
    
    await _attach_step_images("Uni knot", plan)
    
    # Overview should NOT have images attached
    overview = plan["lesson_plan"][0]
    assert "images" not in overview or not overview.get("images")
    
    # Step 1 should have image
    step1 = plan["lesson_plan"][1]
    assert "images" in step1
    assert len(step1["images"]) == 1
    assert step1["images"][0]["url"] == "https://example.org/demo.jpg"
    
    # Step 2 should have image
    step2 = plan["lesson_plan"][2]
    assert "images" in step2
    assert len(step2["images"]) == 1


def test_cardify_step_cards_have_correct_theme():
    """Test that step cards inherit theme from parent."""
    plan = {
        "lesson_plan": [{
            "title": "FG Knot",
            "kind": "howto",
            "theme": "ocean",
            "summary": "Leader knot",
            "steps": [
                {"title": "Setup", "body": "Position lines."},
                {"title": "Wrap", "body": "Braid around leader."},
            ],
        }]
    }
    out = _cardify_steps(plan)
    
    # All cards should have ocean theme
    for card in out["lesson_plan"]:
        assert card["theme"] == "ocean"

