"""Provider-agnostic chat-with-tools client over plain HTTP.

Two wire formats cover most options:
- "anthropic": Anthropic Messages API (Claude models)
- "openai":    OpenAI-compatible Chat Completions. Works with OpenAI and with local
               servers that speak the same format (Ollama, llama.cpp server, LM Studio)
               by pointing LLM_BASE_URL at them.

Messages use one internal format, converted per provider:
  {"role": "user", "content": str}
  {"role": "assistant", "content": str, "tool_calls": [{"id", "name", "arguments": dict}]}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field

from .http import post_json

DEFAULTS = {
    "anthropic": {"base_url": "https://api.anthropic.com", "model": "claude-sonnet-5-5", "key_env": "ANTHROPIC_API_KEY"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": None, "key_env": "OPENAI_API_KEY"},
}


@dataclass
class Reply:
    text: str
    tool_calls: list[dict]
    raw: dict = field(repr=False, default_factory=dict)
    stop_reason: str = ""   # "max_tokens" (Anthropic) or "length" (OpenAI) means the reply was cut off

    @property
    def truncated(self) -> bool:
        return self.stop_reason in ("max_tokens", "length")


@dataclass
class LLMClient:
    provider: str
    model: str
    base_url: str
    api_key: str | None = None
    max_tokens: int = 8192   # long structured answers need room; LLM_MAX_TOKENS overrides
    temperature: float | None = None   # not sent unless set: newer models reject it
    extra: dict = field(default_factory=dict)   # passed through to the request body

    # ---- public ----------------------------------------------------------------
    def chat(self, system: str, messages: list[dict], tools: list[dict]) -> Reply:
        if self.provider == "anthropic":
            return self._anthropic(system, messages, tools)
        if self.provider == "openai":
            return self._openai(system, messages, tools)
        raise ValueError(f"Unknown provider {self.provider!r}; use 'anthropic' or 'openai'")

    def describe(self) -> str:
        return f"{self.provider}:{self.model} @ {self.base_url}"

    # ---- Anthropic Messages API ------------------------------------------------------
    def _anthropic(self, system, messages, tools) -> Reply:
        converted = []
        for m in messages:
            if m["role"] == "user":
                converted.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                blocks = [{"type": "text", "text": m["content"]}] if m.get("content") else []
                blocks += [{"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["arguments"]}
                           for c in m.get("tool_calls", [])]
                converted.append({"role": "assistant", "content": blocks})
            elif m["role"] == "tool":
                result = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
                if converted and converted[-1]["role"] == "user" and isinstance(converted[-1]["content"], list):
                    converted[-1]["content"].append(result)   # results of parallel calls share one turn
                else:
                    converted.append({"role": "user", "content": [result]})
        body = {
            "model": self.model, "max_tokens": self.max_tokens, "system": system, "messages": converted,
            "tools": [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in tools],
            **({"temperature": self.temperature} if self.temperature is not None else {}),
            **self.extra,
        }
        headers = {"x-api-key": self.api_key or "", "anthropic-version": "2023-06-01"}
        raw = post_json(self.base_url.rstrip("/") + "/v1/messages", body, headers=headers, timeout=180)
        text = "".join(b.get("text", "") for b in raw.get("content", []) if b.get("type") == "text")
        calls = [{"id": b["id"], "name": b["name"], "arguments": b.get("input") or {}}
                 for b in raw.get("content", []) if b.get("type") == "tool_use"]
        return Reply(text, calls, raw, stop_reason=raw.get("stop_reason") or "")

    # ---- OpenAI-compatible Chat Completions --------------------------------------
    def _openai(self, system, messages, tools) -> Reply:
        converted = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "user":
                converted.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                msg = {"role": "assistant", "content": m.get("content") or ""}
                if m.get("tool_calls"):
                    msg["tool_calls"] = [{"id": c["id"], "type": "function",
                                          "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
                                         for c in m["tool_calls"]]
                converted.append(msg)
            elif m["role"] == "tool":
                converted.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
        body = {
            "model": self.model, "messages": converted,
            "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                        "parameters": t["parameters"]}} for t in tools],
            **({"temperature": self.temperature} if self.temperature is not None else {}),
            **self.extra,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        raw = post_json(self.base_url.rstrip("/") + "/chat/completions", body, headers=headers, timeout=300)
        msg = raw["choices"][0]["message"]
        calls = []
        for c in msg.get("tool_calls") or []:
            fn = c.get("function", {})
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except json.JSONDecodeError:
                    args = {"_unparseable_arguments": args}
            calls.append({"id": c.get("id") or f"call_{uuid.uuid4().hex[:8]}", "name": fn.get("name"), "arguments": args})
        return Reply(msg.get("content") or "", calls, raw, stop_reason=raw["choices"][0].get("finish_reason") or "")


def from_env(**overrides) -> LLMClient:
    """Build a client from LLM_PROVIDER, LLM_MODEL, LLM_BASE_URL and the provider's API key variable.

    Local servers: LLM_PROVIDER=openai, LLM_BASE_URL=http://host.docker.internal:11434/v1 (Ollama),
    LLM_MODEL=<a tool-calling model you have pulled>. No key needed.
    """
    provider = overrides.pop("provider", None) or os.environ.get("LLM_PROVIDER", "anthropic")
    if provider not in DEFAULTS:
        raise ValueError(f"LLM_PROVIDER must be one of {list(DEFAULTS)}, got {provider!r}")
    d = DEFAULTS[provider]
    model = overrides.pop("model", None) or os.environ.get("LLM_MODEL") or d["model"]
    if not model:
        raise ValueError(f"Set LLM_MODEL for provider {provider!r}")
    base_url = overrides.pop("base_url", None) or os.environ.get("LLM_BASE_URL") or d["base_url"]
    api_key = overrides.pop("api_key", None) or os.environ.get(d["key_env"]) or os.environ.get("LLM_API_KEY")
    is_local = provider == "openai" and base_url != d["base_url"]
    if not api_key and not is_local:
        raise ValueError(f"No API key: set {d['key_env']} (or LLM_API_KEY)")
    if "max_tokens" not in overrides and os.environ.get("LLM_MAX_TOKENS"):
        overrides["max_tokens"] = int(os.environ["LLM_MAX_TOKENS"])
    if "temperature" not in overrides and os.environ.get("LLM_TEMPERATURE"):
        overrides["temperature"] = float(os.environ["LLM_TEMPERATURE"])
    return LLMClient(provider=provider, model=model, base_url=base_url, api_key=api_key, **overrides)
