from __future__ import annotations
from typing import Any, Union
from pydantic import BaseModel
from apps.api.orchestrator import two_pass_answer

class ChatRequest(BaseModel):
    query: str
    message: str = ""  # Support both field names

async def run_chat(req: Union[ChatRequest, dict, str]) -> Any:
    """Legacy shim → delegates to two_pass_answer(user_prompt)."""
    if isinstance(req, ChatRequest):
        user_prompt = req.query or req.message
    elif isinstance(req, dict):
        user_prompt = req.get("query") or req.get("message") or str(req)
    else:
        user_prompt = str(req)
    return await two_pass_answer(user_prompt)
