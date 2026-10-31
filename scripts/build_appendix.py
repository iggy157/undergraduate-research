"""Build docs/APPENDIX.md: everything that may go into a paper appendix, in one file — conditions and settings,
the prompt templates and rendered prompts taken from the recorded games, the judge instructions, the metric
definitions, and every detailed result table (copied from the result documents, which stay the source).

usage: python scripts/build_appendix.py [--out docs/APPENDIX.md]
Re-run after a result document changes; the file is generated, do not edit it by hand.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FENCE = "````"


def code(text: str, lang: str = "") -> str:
    return f"{FENCE}{lang}\n{text.rstrip()}\n{FENCE}\n"


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else f"(missing: {rel})"


def demote(md: str, by: int = 2) -> str:
    """Push the headings of an included document down so that it nests under the appendix heading."""
    out = []
    in_code = False
    for line in md.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,4} ", line):
            line = "#" * by + line
        out.append(line)
    return "\n".join(out)


def include(rel: str, title: str | None = None, by: int = 2) -> str:
    head = f"\n#### {title}\n\n" if title else ""
    return head + f"_Source: `{rel}`_\n\n" + demote(read(rel), by) + "\n"


def first_call(game_glob: str, request: str | None = None, nth: int = 0, round_no: int | None = None, seat: int | None = None):
    fs = sorted(glob.glob(str(ROOT / game_glob)))
    if not fs:
        return None, None
    recs = [json.loads(l) for l in open(fs[0], encoding="utf-8")]
    calls = [r for r in recs if r.get("kind") == "llm_call" and (request is None or r.get("request") == request)
             and (round_no is None or r.get("round") == round_no) and (seat is None or r.get("seat") == seat)]
    if len(calls) <= nth:
        return None, fs[0]
    return calls[nth], fs[0]


def render_call(title: str, game_glob: str, request: str | None = None, nth: int = 0, round_no: int | None = None,
                seat: int | None = None, roles: tuple[str, ...] = ("system", "user", "assistant"), max_chars: int | None = None) -> str:
    call, path = first_call(game_glob, request, nth, round_no, seat)
    if call is None:
        return f"\n#### {title}\n\n(no recorded call for `{game_glob}`)\n"
    rel = Path(path).relative_to(ROOT)
    out = [f"\n#### {title}\n", f"_Recorded call: `{rel}`, seat {call.get('seat')}, request {call.get('request')}, "
           f"round {call.get('round')}, turn {call.get('turn')}._\n"]
    for m in call["messages"]:
        if m["role"] not in roles:
            continue
        txt = m["content"]
        if max_chars and len(txt) > max_chars:
            txt = txt[:max_chars] + f"\n… ({len(m['content']) - max_chars} more characters)"
        out.append(f"**{m['role']}**\n")
        out.append(code(txt))
    if call.get("response") is not None:
        out.append("**model output (recorded)**\n")
        out.append(code(str(call["response"])[:3000]))
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/APPENDIX.md")
    a = ap.parse_args(argv)
    G = "log/main_gemma31b"
    parts: list[str] = []
    P = parts.append
    P(f"# Appendix material (generated {_dt.date.today().isoformat()} by `scripts/build_appendix.py`)\n")
    P("Everything that may go into a paper appendix, in one place: conditions and settings (A), prompts (B), "
      "judging (C), metrics (D), detailed results (E), reproducibility notes (F). Result sections are copies of the "
      "result documents named under each heading; those documents and the logs stay the source.\n")

    # ---------------------------------------------------------------- A
    P("## A. Conditions, models and settings\n")
    P("### A.1 Names\n")
    P("| presentation name | condition (code / logs) | writer | information | generation goal |\n|---|---|---|---|---|\n"
      "| シングル・全文 | single-batch | one LLM | all (omniscient) | whole script in one call |\n"
      "| (control) | single-batch-stepped | one LLM | all | the whole-script request, continued one line per call |\n"
      "| シングル・1 発話 | single-online | one LLM | all | next line only |\n"
      "| マルチ・全文 | multi-private-stepped (multi-batch) | one LLM per seat | own seat | whole-script request, the seat's next line only is kept |\n"
      "| マルチ・1 発話 | multi-private (multi-online) | one LLM per seat | own seat | next line only |\n"
      "| (omniscient seats) | multi-public, multi-public-stepped | one LLM per seat | all | next line / whole-script request |\n"
      "| (plan) | *-process | as the base condition | + a process plan without the outcome | as the base |\n")
    P("\nFew-shot conditions (DESIGN §16): single-batch and multi-private with 3 discussion examples of the model's own "
      "(short = its single-batch games, long = its multi-private games; other setups of the same domain, the first 3 in "
      "setup order, the target setup excluded), logs under `log/fewshot/<model>__ex-<short|long>/`. Goal swap: recorded "
      "states re-generated under the other goal (`log/goal_swap/`); examples vs history: long-history states with 3 short "
      "examples (`log/goal_swap_ex/`).\n")
    P("### A.2 Design document\n")
    P(include("docs/DESIGN.md", by=2))
    P("### A.3 Model configuration (config/models.yml)\n")
    P(code(read("config/models.yml"), "yaml"))
    P("### A.4 Server settings\n")
    P("- vLLM 0.21.1rc1, transformers 5.8.1, NVIDIA RTX PRO 6000 Blackwell (96 GB). Temperature 0 everywhere.\n"
      "- gemma-4-31B-it: `VLLM_BATCH_INVARIANT=1` (identical outputs across batches and instances), max-model-len 20480 "
      "(32768 for the few-shot runs; output ceilings unchanged).\n"
      "- Qwen3.8-27B: batch-invariant mode unsupported (linear attention); `--max-num-seqs 1 --no-enable-prefix-caching "
      "--default-chat-template-kwargs {\"enable_thinking\":false}`, every call of a setup on the same instance "
      "(`run_queue.py --pin-by-setup`); outputs identical within an instance (90/90 repeated games), not across instances.\n"
      "- Judges: Llama 3.3 70B Instruct (bf16, tensor parallel 2) and gpt-oss-120b (MXFP4), temperature 0, families "
      "different from the generators.\n")
    P("Server start scripts used for the runs are kept under `log/stage_scripts/` (copies of the session's orchestration).\n")
    P(code(read("log/stage_scripts/stage/gemma_one.sh"), "bash"))
    P(code(read("log/stage_scripts/qwen/start_vllm_qwen.sh"), "bash"))
    P(code(read("log/stage_scripts/llama/start_vllm_llama.sh"), "bash"))
    P(code(read("log/stage_scripts/llama/start_vllm_gptoss.sh"), "bash"))

    # ---------------------------------------------------------------- B
    P("## B. Prompts\n")
    P("### B.1 Templates (source)\n")
    for f in sorted(glob.glob(str(ROOT / "common/prompts/*.jinja"))) + sorted(glob.glob(str(ROOT / "single/prompts/*.jinja"))) + \
            sorted(glob.glob(str(ROOT / "agent/prompts/*.jinja"))) + sorted(glob.glob(str(ROOT / "scripts/prompts/*.jinja"))):
        rel = Path(f).relative_to(ROOT)
        P(f"\n#### `{rel}`\n")
        P(code(Path(f).read_text(encoding="utf-8"), "jinja"))
    P("\nPrompt assembly: `common/render.py` (`system_prompt`: role + shared blocks + participants/hidden information or the "
      "seat's own profile + plan block), `single/base/prompt.py` (`build_messages`), `agent/base/prompts.py` "
      "(`build_system_prompt`, `build_talk_message`), `agent/base/seat.py` (stepped seats: the participant's system "
      "prompt + the single-batch request + the seat's own transcript continued as the assistant's output, stopped at the "
      "next line label), `common/examples.py` (the few-shot block).\n")
    P(code(read("common/render.py")[read("common/render.py").find("def system_prompt"):][:2500], "python"))
    P("### B.2 Rendered prompts (Werewolf aiwolf_0001, gemma-4-31B, recorded)\n")
    P(render_call("シングル・全文 (single-batch): the whole-script request", f"{G}/aiwolf/single-batch/aiwolf_0001__single-batch__*/*.jsonl", "FULL", max_chars=None))
    P(render_call("シングル・1 発話 (single-online): the writer's next-line request, first turn", f"{G}/aiwolf/single-online/aiwolf_0001__single-online__*/*.jsonl", "TALK"))
    P(render_call("マルチ・1 発話 (multi-private): a seat, first turn", f"{G}/aiwolf/multi-private/aiwolf_0001__multi-private__*/*.jsonl", "TALK"))
    P(render_call("マルチ・1 発話 (multi-private): the same seat later in the game (transcript format)", f"{G}/aiwolf/multi-private/aiwolf_0001__multi-private__*/*.jsonl", "TALK", round_no=1, seat=1, roles=("user",)))
    P(render_call("Omniscient seat (multi-public): first turn", f"{G}/aiwolf/multi-public/aiwolf_0001__multi-public__*/*.jsonl", "TALK"))
    P(render_call("マルチ・全文 (multi-private-stepped): a seat, later turn (system omitted: as multi-private)", f"{G}/aiwolf/multi-private-stepped/aiwolf_0001__multi-private-stepped__*/*.jsonl", "TALK", round_no=1, roles=("user", "assistant")))
    P(render_call("Control single-batch-stepped: a later call (system omitted: as single-batch)", f"{G}/aiwolf/single-batch-stepped/aiwolf_0001__single-batch-stepped__*/*.jsonl", "TALK", round_no=1, roles=("assistant",), max_chars=4000))
    P(render_call("Plan condition (multi-private-process): a seat's system prompt with the plan block", f"{G}/aiwolf/multi-private/aiwolf_0001__multi-private-process__*/*.jsonl", "TALK", roles=("system",)))
    P(render_call("Vote request (multi-private)", f"{G}/aiwolf/multi-private/aiwolf_0001__multi-private__*/*.jsonl", "VOTE", roles=("user",)))
    for req in ("DIVINE", "ATTACK"):
        P(render_call(f"Night action request ({req})", f"{G}/aiwolf/multi-private/aiwolf_0001__multi-private__*/*.jsonl", req, roles=("user",)))
    P("### B.3 Rendered prompts (discussion domains, gemma-4-31B, recorded)\n")
    for dom, sid in (("candidate_selection", "candidate_selection_0001"), ("shared_living", "shared_living_0001")):
        P(render_call(f"{dom}: シングル・全文 (single-batch)", f"{G}/{dom}/single-batch/{sid}__single-batch__*/*.jsonl", "FULL"))
        P(render_call(f"{dom}: マルチ・1 発話 (multi-private), first turn", f"{G}/{dom}/multi-private/{sid}__multi-private__*/*.jsonl", "TALK"))
    P("### B.4 Few-shot example block (gemma, short examples, aiwolf_0001, multi-private seat)\n")
    P(render_call("A seat's system prompt with the example block (truncated)", "log/fewshot/gemma__ex-short/aiwolf/multi-private/aiwolf_0001__multi-private__*/*.jsonl", "TALK", roles=("system",), max_chars=6000))
    P(code(read("common/examples.py"), "python"))
    P("### B.5 Plans (筋書き) — generation prompt and an example\n")
    P(code(read("scripts/prompts/scenario_request.jinja"), "jinja"))
    plan = ROOT / "scenarios/aiwolf/aiwolf_0001.json"
    P(code(plan.read_text(encoding="utf-8") if plan.exists() else "(missing)", "json"))
    P("### B.6 Goal swap and steering framings\n")
    P("Goal swap (`scripts/goal_swap.py`): a recorded talk call's state (system prompt + transcript so far + the seat's "
      "label) is framed online = [system, user = transcript + label] (chat completion) or batch = [system, user = the "
      "single-batch request] + transcript + label as the assistant's own output (continuation, `/v1/completions`), greedy, "
      "stop strings `\\n- **`, `\\n####`, `\\n###`, `\\n##`. Steering pilots (`scripts/steer_goal2.py`): contrastive "
      "activation addition of the mean batch − online residual at the label's colon (same token in both framings), added "
      "from the label position on; v1 (`steer_goal.py`, contrast at the last prompt token) was discarded.\n")

    # ---------------------------------------------------------------- C
    P("## C. Judging\n")
    P("### C.1 Whole-transcript annotation (main and few-shot runs)\n")
    P(code(read("scripts/prompts/ANNOTATION_INSTRUCTIONS_v2.md"), "markdown"))
    P("Rendered input (excerpt of one game file given to the judge):\n")
    gm = sorted(glob.glob(str(ROOT / "log/annotation/annot_main/games/aiwolf_0001__multi-private.md")))
    P(code("\n".join(Path(gm[0]).read_text(encoding="utf-8").splitlines()[:25]) if gm else "(missing)", "markdown"))
    P("### C.2 Line judge (goal swap, examples vs history): the same five items for the last line\n")
    P(code(read("scripts/prompts/LINE_JUDGE_v2.md"), "markdown"))
    P("`LINE_JUDGE_v1.md` (content / padded / a direct answer question) was used for 40 minutes and discarded because "
      "its items differed from the annotation guide; its outputs are in `log/line_judge/v1_items_mismatch/`.\n")
    P("### C.3 Agreement\n")
    P(include("docs/main_gemma31b/line_judge_summary.md", "Line judge, gemma (incl. Llama vs gpt-oss and line vs whole-transcript)", by=3))
    P(include("docs/main_qwen38/line_judge_summary.md", "Line judge, Qwen", by=3))

    # ---------------------------------------------------------------- D
    P("## D. Metric definitions\n")
    P("- **words / utterance**: whitespace tokens of the talk line (Skip / Over = 0; the line cap is 40 words in the prompts).\n"
      "- **new contributions per 100 words**: content count of the annotation (0-2 per line) summed per game / words × 100 "
      "(the slides' 新情報; `words per content` in the tables is its inverse).\n"
      "- **named-question answer rate** (`addressee's next line responds`): for every line with `?` and `@Name`, whether the "
      "addressee's next line in the period has `resp_to` = that question (any response type).\n"
      "- **unanswered named questions / game**: those questions whose addressee speaks again in the period without responding.\n"
      "- **非公開情報の先出し (early_option)**: share of discussion-domain games in which a full option name is said before the "
      "reveal round; **seer_first_wolf**: Werewolf, the Seer's night-0 target is the werewolf (chance 0.25).\n")
    em = read("scripts/eval_metrics.py")
    P(code(em[: em.find('"""', 3) + 3], "python"))
    P(code(read("scripts/annotation_qa.py")[:1500], "python"))

    # ---------------------------------------------------------------- E
    P("## E. Detailed results\n")
    P("### E.1 Main runs: annotations\n")
    P(include("docs/main_gemma31b/annotation/summary_all.md", "gemma-4-31B (900 games)", by=3))
    P(include("docs/main_gemma31b/annotation/qa_all.md", "gemma-4-31B: named questions", by=3))
    P(include("docs/main_qwen38/annotation/summary_all.md", "Qwen3.8-27B (630 games)", by=3))
    P(include("docs/main_qwen38/annotation/qa_all.md", "Qwen3.8-27B: named questions", by=3))
    P("### E.2 Main runs: automatic metrics\n")
    P(include("docs/main_gemma31b/metrics_summary_all.md", "gemma-4-31B", by=3))
    P(include("docs/main_qwen38/metrics_summary_all.md", "Qwen3.8-27B", by=3))
    P("### E.3 Hidden-state probes\n")
    for m in ("main_gemma31b", "main_qwen38"):
        P(include(f"docs/{m}/probe_summary_v2.md", f"{m}: v2 (words and other targets, nested CV)", by=3))
        P(include(f"docs/{m}/probe_summary_v3.md", f"{m}: v3 (content, question answering, layer curves, transfer)", by=3))
    P("### E.4 Goal swap on identical histories\n")
    for m in ("main_gemma31b", "main_qwen38"):
        P(include(f"docs/{m}/goal_swap_summary.md", f"{m}: lengths", by=3))
        P(include(f"docs/{m}/swap_probe.md", f"{m}: length probe on identical histories", by=3))
    P("### E.5 Steering pilots\n")
    P(include("docs/steering_2026-10-30/summary.md", by=3))
    P("### E.6 Few-shot examples and examples vs history\n")
    P(include("docs/fewshot_2026-10-30/README.md", "Summary", by=3))
    for d in ("gemma__ex-short", "gemma__ex-long", "qwen__ex-short", "qwen__ex-long"):
        P(include(f"docs/fewshot_2026-10-30/annotation_{d}.md", f"{d}: annotations", by=3))
        P(include(f"docs/fewshot_2026-10-30/qa_{d}.md", f"{d}: named questions", by=3))
        P(include(f"docs/fewshot_2026-10-30/probe_{d}.md", f"{d}: probes (all lines)", by=3))
    for d in ("gemma-none", "gemma-short", "gemma-long", "qwen-none", "qwen-short", "qwen-long"):
        P(include(f"docs/fewshot_2026-10-30/probe_talkonly_{d}.md", f"{d}: length probe, talk lines only", by=3))
    for m in ("gemma", "qwen"):
        P(include(f"docs/tug_2026-10-31/probe_{m}.md", f"examples vs history, {m}: length probe on identical states", by=3))
    P("### E.7 Japanese summaries written along the way\n")
    P(include("docs/progress_report_2026-10-29/hidden_states_2026-10-30.md", by=3))

    # ---------------------------------------------------------------- F
    P("## F. Reproducibility notes\n")
    P("- Determinism: gemma outputs are identical across instances under `VLLM_BATCH_INVARIANT=1`; Qwen only within an "
      "instance (every call of a setup pinned to one instance). Judges are not batch invariant (temperature 0).\n"
      "- Hidden states are replays of the recorded token ids (`scripts/extract_hidden.py`); sequences over 8,000 tokens "
      "(7,000 in `swap_hidden.py`) are computed in 1,024-token chunks with the KV cache carried over (cosine to the "
      "one-pass value ≥ 0.9998 at layers 20/40, 0.993 at the last layer); such calls are listed in the index files.\n"
      "- Excluded: single-batch games whose script lines could not be matched to the gen-point positions (gemma 18, "
      "Qwen 38) in the probes; unparsed line-judge replies (gemma 0.5%, Qwen 1.1%).\n"
      "- Plan conditions for Qwen were first generated with gemma's plans; those games are set aside in "
      "`log/main_qwen38_gemmaplans/` and not used. Qwen's own plans passed validation for 56/90 setups only; the plan "
      "conditions are reported for gemma.\n"
      "- The short- and long-example runs started in the same second, so a game id can occur in both folders; the folder "
      "tells them apart.\n"
      "- Annotation outputs and the session's orchestration scripts are kept in `log/annotation/` and `log/stage_scripts/`.\n")
    P(include("docs/IMPLEMENTATION_NOTES.md", "Implementation notes", by=3))

    text = "\n".join(parts) + "\n"
    # the session scratchpad held the annotation directories; they are kept under log/annotation/ now
    text = re.sub(r"/tmp/claude-[^ ]*?/scratchpad/(annot_main|annot_qwen|annot_fewshot)", r"log/annotation/\1", text)
    text = re.sub(r"/tmp/claude-[^ ]*?/scratchpad/", "log/stage_scripts/", text)
    out = ROOT / a.out
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out} ({len(text):,} characters, {text.count(chr(10)):,} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
