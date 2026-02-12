"""LLM 클라이언트 - Gemini / Groq / Grok / Ollama 지원 (동기 전용)

Django 동기 뷰 기반이므로 async를 제거하고 직접 동기 호출합니다.
기존 asyncio.to_thread() 래핑이 불필요해져 코드가 단순화됩니다.
"""

import json
from typing import Any

from django.conf import settings


def _gemini_style_to_openai_tools(tools: list[dict]) -> list[dict]:
    """Gemini 형식 도구 → OpenAI/Groq/Grok 형식."""
    out = []
    for t in tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get(
                        "parameters", {"type": "object", "properties": {}}
                    ),
                },
            }
        )
    return out


def _chat_gemini(messages: list[dict], tools: list[dict] | None) -> dict:
    from google import genai
    from google.genai import types

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env에 추가하세요.")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    config_kwargs: dict = {"temperature": 0}
    if tools:
        tool_objs = [types.Tool(function_declarations=tools)]
        config_kwargs["tools"] = tool_objs
        config_kwargs["automatic_function_calling"] = (
            types.AutomaticFunctionCallingConfig(disable=True)
        )
    config = types.GenerateContentConfig(**config_kwargs)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_msg,
        config=config,
    )

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


def _chat_openai_style(
    provider: str,
    api_key: str,
    model: str,
    base_url: str | None,
    messages: list[dict],
    tools: list[dict] | None,
) -> dict:
    """Ollama / Groq / Grok(OpenAI 호환) 공통."""
    from openai import OpenAI

    if provider != "ollama" and not api_key:
        raise ValueError(
            f"{provider.upper()}_API_KEY가 설정되지 않았습니다. .env에 추가하세요."
        )
    kwargs = {"api_key": api_key or "ollama"}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    openai_tools = _gemini_style_to_openai_tools(tools) if tools else None

    chat_messages: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            chat_messages.append({"role": "system", "content": content})
        else:
            chat_messages.append({"role": role, "content": content})
    if not chat_messages:
        chat_messages.append({"role": "user", "content": ""})

    kwargs_create = {"model": model, "messages": chat_messages, "temperature": 0}
    if openai_tools:
        kwargs_create["tools"] = openai_tools
        kwargs_create["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs_create)
    msg = response.choices[0].message
    content = msg.content
    function_call = None
    if getattr(msg, "tool_calls", None) and len(msg.tool_calls) > 0:
        tc = msg.tool_calls[0]
        fn = getattr(tc, "function", None)
        if fn:
            name = getattr(fn, "name", None) or (
                fn.get("name") if isinstance(fn, dict) else None
            )
            args_str = (
                getattr(fn, "arguments", None)
                or (fn.get("arguments") if isinstance(fn, dict) else None)
                or "{}"
            )
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                args = {}
            function_call = {"name": name, "args": args}
    return {"content": content, "function_call": function_call}


def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
    provider_override: str | None = None,
) -> dict:
    """
    LLM 호출 (provider: ollama 로컬 GPU | gemini | groq | grok).
    동기 함수 — Django 동기 뷰에서 직접 호출.
    """
    provider = (provider_override or settings.LLM_PROVIDER or "groq").strip().lower()
    if provider == "ollama":
        return _chat_openai_style(
            "ollama",
            "",
            settings.OLLAMA_MODEL,
            settings.OLLAMA_BASE_URL,
            messages,
            tools,
        )
    if provider == "gemini":
        return _chat_gemini(messages, tools)
    if provider == "groq":
        return _chat_openai_style(
            "groq",
            settings.GROQ_API_KEY,
            settings.GROQ_MODEL,
            "https://api.groq.com/openai/v1",
            messages,
            tools,
        )
    if provider == "grok":
        return _chat_openai_style(
            "grok",
            settings.GROK_API_KEY,
            settings.GROK_MODEL,
            "https://api.x.ai/v1",
            messages,
            tools,
        )
    raise ValueError(
        f"지원하지 않는 LLM 프로바이더: {provider}. ollama | gemini | groq | grok"
    )
