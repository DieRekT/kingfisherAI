from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from enum import Enum

# Tool call types
class ToolCallType(str, Enum):
    images = "images"
    search = "search"
    weather = "weather"
    marine = "marine"
    tides = "tides"

# Citation for search results and sources
class Citation(BaseModel):
    url: str
    title: str
    snippet: Optional[str] = None

class ImageRef(BaseModel):
    url: str
    alt: Optional[str] = None
    credit: Optional[str] = None
    provider: Optional[str] = None

class LessonStep(BaseModel):
    title: str
    body: str
    image: Optional[ImageRef] = None
    citations: List[Citation] = Field(default_factory=list)

class LessonCard(BaseModel):
    kind: Literal["howto","concept","plan","reference"]
    title: str
    theme: Literal["river","ocean","earth","amber","slate","emerald","indigo"] = "river"
    summary: Optional[str] = None
    steps: List[LessonStep] = Field(default_factory=list)
    images: List[ImageRef] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)

class ChatResponse(BaseModel):
    text: str
    lesson_cards: List[LessonCard] = Field(default_factory=list)
    tool_calls: List[str] = Field(default_factory=list)
    model: str
    took_ms: int
    needs_fresh_facts: bool = False

# JSON Schema for Pass-1 structured output
PASS1_JSON_SCHEMA = {
    "name": "pass1_response",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "needs_fresh_facts": {"type": "boolean"},
            "image_queries": {
                "type": "array",
                "items": {"type": "string"}
            },
            "tool_calls": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["images", "search", "weather", "marine", "tides"]
                }
            },
            "lesson_plan": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": ["howto", "concept", "plan", "reference"]
                        },
                        "title": {"type": "string"},
                        "theme": {
                            "type": "string",
                            "enum": ["river", "ocean", "earth", "amber", "slate", "emerald", "indigo"]
                        },
                        "summary": {"type": "string"},
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "body": {"type": "string"}
                                },
                                "required": ["title", "body"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["kind", "title", "theme", "summary", "steps"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["text", "needs_fresh_facts", "image_queries", "tool_calls", "lesson_plan"],
        "additionalProperties": False
    }
}

