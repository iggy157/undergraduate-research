"""Domain-independent part of the multi-agent client.

- ``prompts``: ``build_system_prompt(ctx, seat)`` and the per-request user messages.
- ``llm``: the injectable ``LLMClient`` interface, the ``openai``-backed ``OpenAILLM`` and ``FakeLLM``.
- ``seat``: ``SeatAgent`` (packet -> reply string, per-seat history, jsonl records).
- ``client``: the websocket loop.
"""
from .client import run_client
from .llm import FakeLLM, LLMClient, ModelConfig, OpenAILLM, load_model_config
from .prompts import (
                      build_action_message,
                      build_system_prompt,
                      build_talk_message,
                      build_vote_message,
                      make_agent_env,
)
from .registry import make_agent
from .seat import LLM_CALL_FIELDS, SeatAgent

__all__ = [
                      "LLM_CALL_FIELDS",
                      "FakeLLM",
                      "LLMClient",
                      "ModelConfig",
                      "OpenAILLM",
                      "SeatAgent",
                      "build_action_message",
                      "build_system_prompt",
                      "build_talk_message",
                      "build_vote_message",
                      "load_model_config",
                      "make_agent",
                      "make_agent_env",
                      "run_client",
]
