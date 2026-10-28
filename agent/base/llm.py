"""LLM access for the multi-agent client.

``LLMClient`` is the injectable interface (one method). ``OpenAILLM`` talks to the OpenAI-compatible
endpoint described in config/models.yml; ``FakeLLM`` returns canned strings for smoke tests.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from common.setup import load_models

Message = dict[str, str]


class LLMClient(Protocol):
    def complete(self, messages: list[Message], max_tokens: int,
                 stop: list[str] | None = None) -> tuple[str, dict[str, Any]]:
        """Return (raw response text, meta). meta may hold finish_reason, usage, model."""
        ...


@dataclass
class ModelConfig:
    name: str
    base_url: str
    api_key: str
    model: str
    temperature: float
    max_tokens: dict[str, int] = field(default_factory=dict)
    timeout_s: float = 600.0
    logprobs: bool = False
    top_p: float | None = None     # None = the server's default
    top_k: int | None = None
    # Technical boundary of the generation unit (not an instruction): a TALK reply ends where the next
    # transcript line would begin. Newlines inside the utterance are allowed.
    stop_talk: tuple[str, ...] = ("\n- **", "\n####", "\n###", "\n##")

    def sampling(self) -> dict[str, Any]:
        """What the header records (DESIGN §3.2): the effective sampling settings of this run."""
        return {"temperature": self.temperature, "top_p": self.top_p, "top_k": self.top_k,
                "max_tokens": dict(self.max_tokens), "timeout_s": self.timeout_s,
                "logprobs": self.logprobs, "stop_talk": list(self.stop_talk)}

    @property
    def model_tag(self) -> str:
        """Last path element of the model name, non [A-Za-z0-9.-] -> '-' (IMPLEMENTATION_NOTES §2)."""
        return re.sub(r"[^A-Za-z0-9.-]", "-", self.model.rsplit("/", 1)[-1])

    def max_tokens_for(self, kind: str) -> int:
        return int(self.max_tokens[kind])


def timeout_for(m: dict[str, Any], method: str = "multi") -> float:
    """``timeout_s`` is a number or ``{multi: s, single: s}`` (audit C4)."""
    t = m.get("timeout_s", 600)
    if isinstance(t, dict):
        return float(t.get(method, t.get("default", 600)))
    return float(t)


def load_model_config(name: str = "default", models: dict[str, Any] | None = None,
                      temperature: float | None = None, top_p: float | None = None,
                      top_k: int | None = None) -> ModelConfig:
    """``temperature`` / ``top_p`` / ``top_k`` override config/models.yml (e.g. 0 for the greedy runs)."""
    cfg = models if models is not None else load_models()
    try:
        m = cfg["models"][name]
    except KeyError as e:
        raise KeyError(f"model {name!r} not in config/models.yml") from e
    ep = cfg["endpoints"][m["endpoint"]]
    key_env = ep.get("api_key_env")
    api_key = (os.environ.get(key_env) if key_env else None) or "EMPTY"
    return ModelConfig(name=name, base_url=str(ep["base_url"]), api_key=api_key, model=str(m["model"]),
                       temperature=float(m.get("temperature", 1.0) if temperature is None else temperature),
                       max_tokens={k: int(v) for k, v in dict(m.get("max_tokens", {})).items()},
                       timeout_s=timeout_for(m, "multi"), logprobs=bool(m.get("logprobs", False)),
                       top_p=(m.get("top_p") if top_p is None else top_p),
                       top_k=(m.get("top_k") if top_k is None else top_k))


class OpenAILLM:
    """chat.completions against an OpenAI-compatible endpoint (vLLM).

    ``complete(messages, max_tokens, stop=None)``: TALK calls pass ``cfg.stop_talk``. If the endpoint rejects
    the logprobs / token-id options, the call is retried once without them and ``meta["logprobs_error"]``
    records why (the run continues; the header shows ``sampling.logprobs``)."""

    def __init__(self, cfg: ModelConfig, max_retries: int = 0):
        from openai import OpenAI  # imported lazily so tests never need the SDK configured
        self.cfg = cfg
        self.client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key, timeout=cfg.timeout_s,
                             max_retries=max_retries)
        self.logprobs_ok = cfg.logprobs

    def complete(self, messages: list[Message], max_tokens: int,
                 stop: list[str] | None = None) -> tuple[str, dict[str, Any]]:
        kw: dict[str, Any] = dict(model=self.cfg.model, messages=messages, max_tokens=max_tokens,
                                  temperature=self.cfg.temperature)
        if self.cfg.top_p is not None:
            kw["top_p"] = float(self.cfg.top_p)
        extra: dict[str, Any] = {"top_k": int(self.cfg.top_k)} if self.cfg.top_k is not None else {}
        if stop:
            kw["stop"] = list(stop)
        meta: dict[str, Any] = {}
        if self.logprobs_ok:
            try:
                r = self.client.chat.completions.create(
                    **kw, logprobs=True, top_logprobs=2, extra_body={**extra, "return_tokens_as_token_ids": True})
            except Exception as e:  # noqa: BLE001 - e.g. an endpoint without these options
                self.logprobs_ok = False
                meta["logprobs_error"] = f"{type(e).__name__}: {e}"
                r = self.client.chat.completions.create(**kw, **({"extra_body": extra} if extra else {}))
        else:
            r = self.client.chat.completions.create(**kw, **({"extra_body": extra} if extra else {}))
        choice = r.choices[0]
        text = choice.message.content or ""
        usage = r.usage.model_dump() if getattr(r, "usage", None) is not None else None
        meta.update({"finish_reason": choice.finish_reason, "usage": usage, "model": r.model})
        toks = tokens_of(choice)
        if toks is not None:
            meta["tokens"] = toks
        try:  # the exact prompt token ids (what the model saw), for the hidden-state replay (DESIGN §14)
            meta["prompt_token_ids"] = self._tokenize({"messages": messages, "add_generation_prompt": True})
        except Exception as e:  # noqa: BLE001 - informational
            meta["prompt_token_ids_error"] = f"{type(e).__name__}: {e}"
        return text, meta


    # ---- single-batch-stepped: the batch prompt continued as the writer's own output ---------------------
    def _tokenize(self, body: dict[str, Any]) -> list[int]:
        """vLLM ``POST /tokenize`` (chat messages with the generation prompt, or plain text)."""
        import json as _json
        import urllib.request
        url = self.cfg.base_url.rstrip("/")
        url = url[: -len("/v1")] if url.endswith("/v1") else url
        req = urllib.request.Request(url + "/tokenize", data=_json.dumps({"model": self.cfg.model, **body}).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.cfg.api_key}"})
        with urllib.request.urlopen(req, timeout=self.cfg.timeout_s) as r:
            return list(_json.loads(r.read().decode())["tokens"])

    def complete_continuation(self, messages: list[Message], prefix: str, max_tokens: int,
                              stop: list[str] | None = None) -> tuple[str, dict[str, Any]]:
        """Continue ``prefix`` (the transcript so far + label) as the assistant's own output of the prompt
        ``messages``: token ids = chat template of ``messages`` with the generation prompt (exactly what the
        batch call was fed, empty thought channel included) + ``prefix`` tokenised as text, sent to
        ``/v1/completions``. Under greedy this reproduces the batch generation token for token until the
        server changes something (the stepped condition, DESIGN §13)."""
        prompt_ids = self._tokenize({"messages": messages, "add_generation_prompt": True})
        prefix_ids = self._tokenize({"prompt": prefix, "add_special_tokens": False}) if prefix else []
        kw: dict[str, Any] = dict(model=self.cfg.model, prompt=prompt_ids + prefix_ids, max_tokens=max_tokens,
                                  temperature=self.cfg.temperature)
        if self.cfg.top_p is not None:
            kw["top_p"] = float(self.cfg.top_p)
        extra: dict[str, Any] = {"top_k": int(self.cfg.top_k)} if self.cfg.top_k is not None else {}
        if stop:
            kw["stop"] = list(stop)
        meta: dict[str, Any] = {"continuation": "completions", "prompt_ids": len(prompt_ids), "prefix_ids": len(prefix_ids),
                                "prompt_token_ids": prompt_ids + prefix_ids}
        if self.logprobs_ok:
            try:
                r = self.client.completions.create(**kw, logprobs=2, extra_body={**extra, "return_tokens_as_token_ids": True})
            except Exception as e:  # noqa: BLE001
                self.logprobs_ok = False
                meta["logprobs_error"] = f"{type(e).__name__}: {e}"
                r = self.client.completions.create(**kw, **({"extra_body": extra} if extra else {}))
        else:
            r = self.client.completions.create(**kw, **({"extra_body": extra} if extra else {}))
        choice = r.choices[0]
        text = choice.text or ""
        usage = r.usage.model_dump() if getattr(r, "usage", None) is not None else None
        meta.update({"finish_reason": choice.finish_reason, "usage": usage, "model": r.model})
        lp = getattr(choice, "logprobs", None)
        toks = getattr(lp, "tokens", None) if lp is not None else None
        lps = getattr(lp, "token_logprobs", None) if lp is not None else None
        tops = getattr(lp, "top_logprobs", None) if lp is not None else None
        if toks:
            meta["tokens"] = []
            for i, t in enumerate(toks):
                d: dict[str, Any] = {"token": t, "logprob": (lps[i] if lps and i < len(lps) else None)}
                top = (tops[i] if tops and i < len(tops) else None) or {}
                alts = sorted(((k, v) for k, v in top.items() if k != t), key=lambda kv: -kv[1])
                if alts:
                    d["alt"] = {"token": alts[0][0], "logprob": alts[0][1]}
                meta["tokens"].append(d)
        return text, meta


def tokens_of(choice: Any) -> list[dict[str, Any]] | None:
    """[{token, logprob}] from an OpenAI/vLLM choice with logprobs (token strings are "token_id:<id>" when
    vLLM was asked for ``return_tokens_as_token_ids``); None when the endpoint sent no logprobs."""
    lp = getattr(choice, "logprobs", None)
    content = getattr(lp, "content", None) if lp is not None else None
    if not content:
        return None
    out = []
    for c in content:
        d: dict[str, Any] = {"token": c.token, "logprob": c.logprob}
        alts = [t for t in (getattr(c, "top_logprobs", None) or []) if getattr(t, "token", None) != c.token]
        if alts:  # the runner-up: how close the greedy choice was (audit 2026-10-28 D/E)
            d["alt"] = {"token": alts[0].token, "logprob": alts[0].logprob}
        out.append(d)
    return out


_CANNED_TALKS = (
    "I would like to hear what everyone else is thinking before I say much.",
    "That matches what I have seen so far, though I am not certain yet.",
    "Skip",
    "Over",
)


class FakeLLM:
    """Deterministic canned replies keyed on the last user message (no network).

    - vote request   -> first candidate
    - investigation  -> first two titles, one per line
    - divine/attack  -> first candidate
    - anything else  -> cycles through two utterances, Skip, Over
    """

    def __init__(self, talks: tuple[str, ...] = _CANNED_TALKS):
        self.talks = tuple(talks)
        self.n_talks = 0
        self.calls: list[tuple[list[Message], int]] = []

    def complete(self, messages: list[Message], max_tokens: int,
                 stop: list[str] | None = None) -> tuple[str, dict[str, Any]]:
        self.calls.append(([dict(m) for m in messages], max_tokens))
        meta = {"finish_reason": "stop", "usage": {"prompt_tokens": 0, "completion_tokens": 0,
                                                   "total_tokens": 0}, "model": "fake"}
        user = messages[-1]["content"] if messages else ""
        head = user.split("\n\n", 1)[0]  # request sentence + candidates (the transcript follows)
        lines = [ln.strip() for ln in head.splitlines()]
        bullets = [ln[2:].strip() for ln in lines if ln.startswith("- ")]
        cand_line = next((ln for ln in lines if ln.startswith("Candidates:")), None)
        if cand_line is not None:
            cands = [c.strip() for c in cand_line[len("Candidates:"):].split(",") if c.strip()]
            return (cands[0] if cands else ""), meta
        if "Investigation request" in head:
            return "; ".join(bullets[:2]), meta
        if bullets and ("request." in head or "request:" in head):
            return bullets[0], meta
        text = self.talks[self.n_talks % len(self.talks)]
        self.n_talks += 1
        return text, meta

    def complete_continuation(self, messages: list[Message], prefix: str, max_tokens: int,
                              stop: list[str] | None = None) -> tuple[str, dict[str, Any]]:
        msgs = list(messages) + [{"role": "assistant", "content": prefix}]
        self.calls.append(([dict(m) for m in msgs], max_tokens))
        meta = {"finish_reason": "stop", "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "model": "fake", "continuation": "fake"}
        return self._continue(msgs), meta

    def _continue(self, messages: list[Message]) -> str:
        """stepped: the label is the last line of the assistant message; names and card titles come from the
        system prompt (## Participants ``Name:`` lines, ## Hidden information ``- Title: text`` card lines)."""
        system = messages[0]["content"]
        prefix = messages[-1]["content"]
        label = prefix.rsplit("\n", 1)[-1]
        names = [ln[len("Name: "):].strip() for ln in system.splitlines() if ln.startswith("Name: ")]
        # participants who spoke in the current period are alive: prefer them as targets
        last_talk = prefix.rsplit("### Talk", 1)[-1]
        spoke = [ln.split("**")[1] for ln in last_talk.splitlines() if ln.startswith("- **") and "**:" in ln]
        alive = [n for n in names if n in spoke] or names
        if label.endswith("**:"):
            text = self.talks[self.n_talks % len(self.talks)]
            self.n_talks += 1
            return " " + text
        own = label.split(":")[-1].split("->")[0].strip().strip("- ").strip() if "->" in label else ""
        if label.startswith("- investigate:"):
            cards = []
            in_cards = False
            for ln in system.splitlines():
                if ln.startswith("Cards ("):
                    in_cards = True
                    continue
                if in_cards and ln.startswith("- ") and ": " in ln:
                    cards.append(ln[2:].split(": ", 1)[0])
                elif in_cards and not ln.strip():
                    break
            return " " + "; ".join(cards[:2])
        if label.startswith("- divine:"):  # the batch-style writer states the result after the name
            others = [n for n in alive if n != own]
            return " " + (others[0] + " (human)" if others else "")
        if label.startswith("- attack:"):
            others = [n for n in alive if n != own]
            return " " + (others[0] if others else "")
        # a vote: a living participant for aiwolf, the first option label for the discussion domains
        if "Candidate" in system or "Option" in system:
            for ln in system.splitlines():
                if ln.startswith("- A: "):
                    return " A"
        return " " + (alive[0] if alive else "")
