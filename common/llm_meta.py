"""What the jsonl header records about the inference environment (audit 2026-10-28 B/E): the served model entry,
the vLLM version, the local snapshot the server loaded (HF revision) and the sha1 of its chat template.
Best effort: every field is None when the endpoint does not answer."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any


def _get(url: str, api_key: str = "EMPTY", timeout: float = 10.0) -> Any:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _local_snapshot(root: str) -> Path | None:
    """The local snapshot directory of ``root``: a path, or a HF model id resolved through the HF cache
    (``models--org--name/refs/main`` -> ``snapshots/<revision>``)."""
    p = Path(root)
    if p.is_dir():
        return p
    import os
    hub = Path(os.environ.get("HF_HUB_CACHE") or (Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"))
    repo = hub / ("models--" + root.replace("/", "--"))
    ref = repo / "refs" / "main"
    if ref.is_file():
        snap = repo / "snapshots" / ref.read_text().strip()
        if snap.is_dir():
            return snap
    snaps = sorted((repo / "snapshots").glob("*")) if (repo / "snapshots").is_dir() else []
    return snaps[-1] if snaps else None


def served_info(base_url: str, model: str, api_key: str = "EMPTY") -> dict[str, Any]:
    """{model_info, vllm_version, model_root, hf_revision, chat_template_sha1, config_sha1}."""
    root_url = base_url.rstrip("/")
    root_url = root_url[: -len("/v1")] if root_url.endswith("/v1") else root_url
    out: dict[str, Any] = {"model_info": None, "vllm_version": None, "model_root": None, "hf_revision": None,
                           "chat_template_sha1": None, "config_sha1": None, "server_config": None}
    # the launcher (vllm-server/start.sh) writes running/<port>.json with GPUs, batch-invariant flag, max len ...
    try:
        port = int(root_url.rsplit(":", 1)[-1])
        cfg = Path("/diskthalys/ssd14ta/yharada/vllm-server/running") / f"{port}.json"
        if cfg.is_file():
            out["server_config"] = json.loads(cfg.read_text())
    except Exception:  # noqa: BLE001
        pass
    try:
        for m in _get(root_url + "/v1/models", api_key).get("data", []):
            if m.get("id") == model:
                out["model_info"] = m
                break
    except Exception:  # noqa: BLE001
        return out
    try:
        out["vllm_version"] = _get(root_url + "/version", api_key).get("version")
    except Exception:  # noqa: BLE001
        pass
    root = (out["model_info"] or {}).get("root")
    p = _local_snapshot(str(root)) if root else None
    if p is not None:
        out["model_root"] = str(p)
        if p.parent.name == "snapshots":
            out["hf_revision"] = p.name
        for key, name in (("chat_template_sha1", "chat_template.jinja"), ("config_sha1", "config.json")):
            f = p / name
            if f.is_file():
                out[key] = hashlib.sha1(f.read_bytes()).hexdigest()
    return out


def code_tree_sha1() -> dict[str, Any]:
    """sha1 over the repository's code, prompts, rules and config (every .py / .jinja / .yml / .yaml file outside
    tests, logs and caches), plus the per-file list's count: the version of the code that produced a record when
    the repository is not under version control (audit 2026-10-28 E round 2)."""
    from . import ROOT
    h = hashlib.sha1()
    n = 0
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.suffix not in (".py", ".jinja", ".yml", ".yaml"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(("tests/", "log/", ".venv/", "scenarios/", "setups/")) or "__pycache__" in rel:
            continue
        h.update(rel.encode()); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
        n += 1
    return {"sha1": h.hexdigest(), "files": n}


__all__ = ["code_tree_sha1", "served_info"]
