"""Multi-agent LLM client (one seat per process). See docs/IMPLEMENTATION_NOTES.md §4.

Public entry points live in ``agent.base``: ``build_system_prompt(ctx, seat)``, ``make_agent``,
``run_client``, ``OpenAILLM`` / ``FakeLLM``.
"""
