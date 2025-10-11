"""
Schema validation test: ensures PASS1_JSON_SCHEMA is valid and accepts conformant data.
"""
import pytest
from apps.api.schemas import PASS1_JSON_SCHEMA
from jsonschema import validate, ValidationError


def test_pass1_json_schema_minimal_plan():
    """Test that a minimal valid plan passes schema validation."""
    minimal = {
        "text": "Here's how to tie a uni knot.",
        "needs_fresh_facts": False,
        "image_queries": ["uni knot fishing"],
        "tool_calls": ["images"],
        "lesson_plan": [
            {
                "kind": "howto",
                "title": "Tying a Uni Knot",
                "theme": "river",
                "summary": "Simple, strong fishing knot",
                "steps": [
                    {"title": "Thread the line", "body": "Pass tag end through eye twice."},
                    {"title": "Wrap", "body": "Make 5 turns around standing line."},
                    {"title": "Tighten", "body": "Pull tag end to snug knot against eye."}
                ]
            }
        ]
    }
    # Should not raise ValidationError (all required fields present)
    validate(instance=minimal, schema=PASS1_JSON_SCHEMA["schema"])


def test_pass1_json_schema_multiple_cards():
    """Test schema with multiple lesson cards and multiple tool calls."""
    plan = {
        "text": "Planning your fishing trip requires checking weather and tides.",
        "needs_fresh_facts": True,
        "image_queries": ["fishing weather", "tide chart"],
        "tool_calls": ["weather", "marine", "images", "search"],
        "lesson_plan": [
            {
                "kind": "plan",
                "title": "Trip Planning",
                "theme": "ocean",
                "summary": "Essential checks before heading out",
                "steps": [
                    {"title": "Check weather", "body": "Look for wind speed and rain forecast."},
                    {"title": "Check tides", "body": "Best fishing is 2 hours either side of high tide."}
                ]
            },
            {
                "kind": "concept",
                "title": "Understanding Tides",
                "theme": "river",
                "summary": "Tidal concepts for fishing",
                "steps": [
                    {"title": "What are tides?", "body": "Rise and fall of sea levels caused by moon and sun gravity."}
                ]
            }
        ]
    }
    # Should not raise ValidationError
    validate(instance=plan, schema=PASS1_JSON_SCHEMA["schema"])


def test_pass1_json_schema_rejects_invalid_step():
    """Test that schema rejects steps with additional properties."""
    invalid = {
        "text": "Test",
        "needs_fresh_facts": False,
        "image_queries": [],
        "tool_calls": [],
        "lesson_plan": [
            {
                "kind": "howto",
                "title": "Test Card",
                "theme": "river",
                "summary": "Test summary",
                "steps": [
                    {
                        "title": "Step 1",
                        "body": "Do something",
                        "image_query": "this field should not be allowed"  # Should fail
                    }
                ]
            }
        ]
    }
    # Should raise ValidationError due to additionalProperties: false
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid, schema=PASS1_JSON_SCHEMA["schema"])
    assert "Additional properties are not allowed" in str(exc_info.value)


def test_pass1_json_schema_rejects_invalid_tool():
    """Test that schema rejects invalid tool names."""
    invalid = {
        "text": "Test",
        "needs_fresh_facts": False,
        "image_queries": [],
        "lesson_plan": [],
        "tool_calls": ["invalid_tool"]  # Not in enum
    }
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid, schema=PASS1_JSON_SCHEMA["schema"])
    assert "'invalid_tool' is not one of" in str(exc_info.value)


def test_pass1_json_schema_requires_text_and_lesson_plan():
    """Test that schema enforces required fields."""
    invalid = {
        "needs_fresh_facts": False,
        # Missing "text" and "lesson_plan"
    }
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid, schema=PASS1_JSON_SCHEMA["schema"])
    assert "'text' is a required property" in str(exc_info.value) or "'lesson_plan' is a required property" in str(exc_info.value)

