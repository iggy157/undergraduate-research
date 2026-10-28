"""Single method: one LLM call writes the whole transcript, which common/convert turns into the log.

Entry points: ``single.base.build_messages(ctx)`` (prompt), ``single.base.run_single(...)`` (full run),
``python -m single`` (CLI). Domain packages (``single.aiwolf`` etc.) only name the format template and
whether the writer-only disclosure block is included.
"""
