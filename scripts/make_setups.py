"""Generate setups/<domain>/<setup_id>.json from config/experiment.yml (DESIGN §4.4).

usage: uv run python scripts/make_setups.py [--n N] [--domains d1,d2] [--info-mode dynamic|fixed] [--force]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.setup import (game_setup, load_experiment, load_instances, load_personas, load_roles,  # noqa: E402
                          save_setup, setup_path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int)
    ap.add_argument("--domains")
    ap.add_argument("--info-mode", choices=["dynamic", "fixed"])
    ap.add_argument("--force", action="store_true", help="overwrite existing setup files")
    a = ap.parse_args()
    exp = load_experiment()
    n = a.n or int(exp["n_setups"])
    domains = a.domains.split(",") if a.domains else list(exp["domains"])
    info_mode = a.info_mode or exp.get("info_mode", "dynamic")
    seed = int(exp["experiment_seed"])
    personas = load_personas()
    for dom in domains:
        roles = load_roles(dom)
        instances = load_instances(dom)
        if dom != "aiwolf" and n % len(instances) != 0:
            print(f"warning: {dom}: n={n} is not a multiple of {len(instances)} instances", file=sys.stderr)
        for k in range(1, n + 1):
            s = game_setup(dom, k, seed, info_mode, personas, roles, instances)
            p = setup_path(dom, s.setup_id)
            if p.exists() and not a.force:
                existing = p.read_text(encoding="utf-8")
                import json
                if json.loads(existing) != s.to_dict():
                    print(f"error: {p} exists and differs (use --force)", file=sys.stderr)
                    return 1
                continue
            save_setup(s)
        print(f"{dom}: {n} setups -> {setup_path(dom, '').parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
