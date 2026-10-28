"""single.base: prompt assembly, LLM clients, the run and a canned transcript. Domain-neutral."""
from .fake import canned_transcript
from .llm import FakeLLM, LLMClient, OpenAIClient, model_config, model_tag
from .prompt import SHARED_BLOCKS, build_messages, disclosure_block, format_block, make_single_env
from .run import METHOD, SingleRun, make_game_id, run_single

__all__ = [
    "METHOD",
    "SHARED_BLOCKS",
    "FakeLLM",
    "LLMClient",
    "OpenAIClient",
    "SingleRun",
    "build_messages",
    "canned_transcript",
    "disclosure_block",
    "format_block",
    "make_game_id",
    "make_single_env",
    "model_config",
    "model_tag",
    "run_single",
]
