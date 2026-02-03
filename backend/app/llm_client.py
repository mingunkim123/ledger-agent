"""LLM 클라이언트 (Step 8-2) - Google Gemini API + function calling"""
import asyncio

from google import genai
from google.genai import types

from app.config import settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Gemini 클라이언트 반환"""
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env에 추가해주세요.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def chat_completion(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """
    Google Gemini Chat Completion 호출.
    messages: [{"role": "user", "content": "..."}]
    tools: function declarations (Gemini 형식)
    반환: {"content": str|None, "function_call": {"name": str, "args": dict}|None}
    """
    client = _get_client()
    user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

    # tools가 있으면 GenerateContentConfig에 포함
    config_kwargs: dict = {"temperature": 0}
    if tools:
        tool_objs = [types.Tool(function_declarations=tools)]
        config_kwargs["tools"] = tool_objs
        config_kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)

    config = types.GenerateContentConfig(**config_kwargs)

    def _generate():
        return client.models.generate_content(
            model=settings.gemini_model,
            contents=user_msg,
            config=config,
        )

    response = await asyncio.to_thread(_generate)

    # function_call 확인
    function_call = None
    if response.candidates and response.candidates[0].content.parts:
        part = response.candidates[0].content.parts[0]
        if hasattr(part, "function_call") and part.function_call:
            fc = part.function_call
            function_call = {"name": fc.name, "args": dict(fc.args) if fc.args else {}}

    return {
        "content": response.text if response.text else None,
        "function_call": function_call,
    }
