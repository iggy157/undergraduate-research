"""LLM clients for the single method: ``complete(messages, max_tokens) -> (text, meta)``.

meta keys: usage (dict | None), finish_reason (str | None), latency_ms (int), error (str | None),
model (str). ``OpenAIClient`` talks to the OpenAI-compatible endpoint from config/models.yml;
``FakeLLM`` returns a canned text (tests, ``--fake``). No client is instantiated at import time.
"""
from __future__ import annotations

import os
import re
import time
from typing import Any, Protocol

from common.setup import load_models


class LLMClient(Protocol):
    def complete(self, messages: list[dict[str, str]], max_tokens: int) -> tuple[str, dict[str, Any]]: ...


def model_config(name: str = "default") -> tuple[dict[str, Any], dict[str, Any]]:
    """(model entry, endpoint entry) from config/models.yml."""
    cfg = load_models()
    try:
        m = dict(cfg["models"][name])
    except KeyError as e:
        raise KeyError(f"model {name!r} not in config/models.yml") from e
    ep = dict(cfg["endpoints"][m["endpoint"]])
    return m, ep


def timeout_for(model: dict[str, Any], method: str) -> float:
    """``timeout_s`` is a number or ``{multi: s, single: s}`` (the single call is much longer, audit C4)."""
    t = model.get("timeout_s", 600)
    if isinstance(t, dict):
        return float(t.get(method, t.get("default", 600)))
    return float(t)


def model_tag(model_name: str) -> str:
    """Last path element of the model name, with [^A-Za-z0-9.-] -> '-' (IMPLEMENTATION_NOTES §2)."""
    last = str(model_name).rstrip("/").split("/")[-1]
    return re.sub(r"[^A-Za-z0-9.-]", "-", last) or "model"


class FakeLLM:
    """Returns a fixed text; records the messages it was given."""

    def __init__(self, text: str, finish_reason: str = "stop", model: str = "fake"):
        self.text = text
        self.finish_reason = finish_reason
        self.model = model
        self.calls: list[tuple[list[dict[str, str]], int]] = []

    def complete(self, messages: list[dict[str, str]], max_tokens: int) -> tuple[str, dict[str, Any]]:
        self.calls.append((messages, max_tokens))
        return self.text, {"usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                           "finish_reason": self.finish_reason, "latency_ms": 0, "error": None,
                           "model": self.model}


class OpenAIClient:
    """chat.completions against config/models.yml (endpoint base_url, model, temperature, timeout_s)."""

    def __init__(self, model: dict[str, Any], endpoint: dict[str, Any], temperature: float | None = None,
                 top_p: float | None = None, top_k: int | None = None):
        self.model = str(model["model"])
        self.temperature = float(model.get("temperature", 1.0) if temperature is None else temperature)
        self.top_p = model.get("top_p") if top_p is None else top_p
        self.top_k = model.get("top_k") if top_k is None else top_k
        self.timeout_s = timeout_for(model, "single")
        self.logprobs = bool(model.get("logprobs", False))
        self.max_tokens_cfg = {k: int(v) for k, v in dict(model.get("max_tokens", {})).items()}
        self.base_url = str(endpoint["base_url"])
        self.api_key = os.environ.get(str(endpoint.get("api_key_env", "")), "") or "EMPTY"
        self._client = None

    @classmethod
    def from_config(cls, name: str = "default", temperature: float | None = None, top_p: float | None = None,
                    top_k: int | None = None) -> OpenAIClient:
        m, ep = model_config(name)
        if m["model"] == "SET_ME":
            raise ValueError(f"config/models.yml: models.{name}.model is SET_ME")
        return cls(m, ep, temperature=temperature, top_p=top_p, top_k=top_k)

    def sampling(self) -> dict[str, Any]:
        return {"temperature": self.temperature, "top_p": self.top_p, "top_k": self.top_k,
                "max_tokens": dict(self.max_tokens_cfg), "timeout_s": self.timeout_s, "logprobs": self.logprobs}

    def model_info(self) -> dict[str, Any] | None:
        """``GET /v1/models`` entry of the served model (id, root, max_model_len ...), best effort."""
        try:
            for m in self._get().models.list().data:
                if getattr(m, "id", None) == self.model:
                    return m.model_dump() if hasattr(m, "model_dump") else dict(m)
        except Exception:  # noqa: BLE001 - informational only
            return None
        return None

    def _get(self):
        if self._client is None:
            from openai import OpenAI  # lazy: tests never import the SDK client
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=self.timeout_s,
                                  max_retries=0)
        return self._client

    def complete(self, messages: list[dict[str, str]], max_tokens: int) -> tuple[str, dict[str, Any]]:
        t0 = time.monotonic()
        meta: dict[str, Any] = {"usage": None, "finish_reason": None, "latency_ms": 0, "error": None,
                                "model": self.model}
        text = ""
        try:
            kw: dict[str, Any] = dict(model=self.model, messages=messages, temperature=self.temperature,
                                      max_tokens=max_tokens)
            if self.top_p is not None:
                kw["top_p"] = float(self.top_p)
            extra: dict[str, Any] = {"top_k": int(self.top_k)} if self.top_k is not None else {}
            if extra:
                kw["extra_body"] = dict(extra)
            if self.logprobs:
                try:
                    resp = self._get().chat.completions.create(
                        **{k: v for k, v in kw.items() if k != "extra_body"}, logprobs=True, top_logprobs=2,
                        extra_body={**extra, "return_tokens_as_token_ids": True})
                except Exception as e:  # noqa: BLE001 - retry once without the logprobs options
                    meta["logprobs_error"] = f"{type(e).__name__}: {e}"
                    resp = self._get().chat.completions.create(**kw)
            else:
                resp = self._get().chat.completions.create(**kw)
            choice = resp.choices[0]
            text = choice.message.content or ""
            meta["finish_reason"] = choice.finish_reason
            lp = getattr(choice, "logprobs", None)
            content = getattr(lp, "content", None) if lp is not None else None
            if content:
                meta["tokens"] = []
                for c in content:
                    d: dict[str, Any] = {"token": c.token, "logprob": c.logprob}
                    alts = [t for t in (getattr(c, "top_logprobs", None) or []) if getattr(t, "token", None) != c.token]
                    if alts:
                        d["alt"] = {"token": alts[0].token, "logprob": alts[0].logprob}
                    meta["tokens"].append(d)
            if resp.usage is not None:
                meta["usage"] = resp.usage.model_dump() if hasattr(resp.usage, "model_dump") else dict(resp.usage)
        except Exception as e:  # noqa: BLE001 - recorded in the jsonl, the run continues with an empty text
            meta["error"] = f"{type(e).__name__}: {e}"
        meta["latency_ms"] = int((time.monotonic() - t0) * 1000)
        try:  # the exact prompt token ids (what the model saw), for the hidden-state replay (DESIGN §14)
            meta["prompt_token_ids"] = self.tokenize_messages(messages)
        except Exception as e:  # noqa: BLE001 - informational
            meta["prompt_token_ids_error"] = f"{type(e).__name__}: {e}"
        return text, meta

    def tokenize_messages(self, messages: list[dict[str, str]]) -> list[int]:
        """vLLM ``POST /tokenize`` of the chat prompt with the generation prompt."""
        import json as _json
        import urllib.request
        url = self.base_url.rstrip("/")
        url = url[: -len("/v1")] if url.endswith("/v1") else url
        req = urllib.request.Request(url + "/tokenize",
                                     data=_json.dumps({"model": self.model, "messages": messages,
                                                       "add_generation_prompt": True}).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
            return [int(x) for x in _json.loads(r.read().decode())["tokens"]]


__all__ = ["FakeLLM", "LLMClient", "OpenAIClient", "model_config", "model_tag", "timeout_for"]
