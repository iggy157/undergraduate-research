"""Scenarios (筋書き, DESIGN §13): a plan of the discussion given to both methods as the ``## Plan`` block.

File: ``scenarios/<domain>/<setup_id>.json``::

    {"setup_id": "aiwolf_0001", "granularity": "turn", "source": {...},
     "periods": [{"period": 0, "public": "...", "divine": "Shizue",
                  "turns": [{"turn": 1, "lines": {"Minako": "...", "Shizue": "...", ...}}, ...]},
                 {"period": 1, "public": "...", "votes": {"Minako": "Shizue", ...}, "executed": "Shizue", ...}],
     "seats": {"Minako": "...", ...},
     "final": {"winner": "VILLAGE"}}                      # discussion: {"adopted": "C"}

Granularity: ``process`` = the public line of every period (what is argued, which way opinion leans) + one line per
participant (stance over time), **without** votes, executions / adoption, night actions or the result (no outcomes,
no secrets: the only plan multi-private may receive); ``outcome`` = the votes, executions / adoption, night actions
and the result only; ``outline`` = process + outcome; ``turn`` = outline + the gist of every line of every turn
(``turns``). A file holds its finest level; ``scenario_view(sc, g)`` derives the others by deletion, so the levels of one
setup never differ in content. The prose (public / seats) must not state an outcome (checked).

``periods[].public`` is what an observer would see (topics, who is suspected, what is decided); ``votes`` the
votes of that period (every vote period), ``executed`` / ``adopted`` what follows from them (checked with the
common tie-break), ``divine`` / ``attack`` the night actions (aiwolf); ``seats`` one line per participant
(stance over time, final vote; the Werewolf's night targets). The plan implies the hidden information, so it
is only used in the reveal conditions (M2 / S1), where both methods see the whole plan verbatim.

``validate_scenario`` replays the plan with the game rules; ``find_scenario_deviations`` compares a played
game's rows with the plan (free play, deviations recorded, never enforced).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from . import ROOT
from .protocol import Role
from .schema import WINNER_VILLAGE, WINNER_WEREWOLF, LogRow
from .setup import GameContext
from .tiebreak import tally

SCENARIOS = ROOT / "scenarios"
GRANULARITIES = ("process", "outcome", "outline", "turn")   # a file holds its finest level; views are derived
DEFAULT_GRANULARITY = "process"
_RANK = {"process": 1, "outcome": 1, "outline": 2, "turn": 3}   # process and outcome are both cut from outline
# words that would put an outcome or a preference into the prose (public lines / seats) of a plan; outcomes belong in
# the fields, and a process plan must not say which option / player the discussion settles on
_OUTCOME_WORDS = re.compile(
    r"\b(executed|execution|lynched|eliminated|adopted|selected|chosen|winner|wins|win|rejected|rejects|reject|"
    r"supports?|supporting|favou?rs?|favou?red|favou?ring|prefers?|preferred|backs?|backed|emerges?|settles?|"
    r"leans?|leaning|sides? with|votes? for|voting for|converges?|consensus|unanimous|agrees? on|decides? on|"
    r"yields? to|gives? in to|the (?:team|group|committee|panel|village)'s (?:need|choice|decision))\b", re.I)
# aiwolf: a process plan must not fix role claims or divinations either (they decide the game as much as a vote)
_AIWOLF_ROLE_WORDS = re.compile(r"\b(seer|werewolf|wolf|wolves|possessed|villager|divin\w*|reveal\w*|claim\w*|accus\w*)\b", re.I)
_LABEL_REF = re.compile(r"\b(?:option|candidate|proposal|plan)\s+([A-D])\b|\b([A-D])\s+(?:is|as|emerges|wins)\b", re.I)
DEVIATION = "deviation"  # violations-record kind of a scenario_deviation item


def scenario_path(domain: str, setup_id: str) -> Path:
    return SCENARIOS / domain / f"{setup_id}.json"


def resolve_scenario(ctx: GameContext, spec: str | Path | None) -> Path:
    """``spec``: a path, or 'auto' / None for scenarios/<domain>/<setup_id>.json."""
    if spec in (None, "", "auto"):
        return scenario_path(ctx.domain, ctx.setup.setup_id)
    p = Path(spec)
    return p if p.is_file() else scenario_path(ctx.domain, str(spec))


def load_scenario(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        sc = json.load(f)
    if not isinstance(sc, dict) or "periods" not in sc:
        raise ValueError(f"{path}: not a scenario file")
    return sc


def scenario_sha1(path: Path) -> str:
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def scenario_header(path: Path, sc: dict[str, Any]) -> dict[str, Any]:
    """What the jsonl header records about the plan used."""
    try:
        rel = str(Path(path).resolve().relative_to(ROOT.resolve()))
    except ValueError:
        rel = str(path)
    return {"path": rel, "sha1": scenario_sha1(path), "granularity": str(sc.get("granularity", DEFAULT_GRANULARITY)),
            "file_granularity": str(sc.get("file_granularity", sc.get("granularity", DEFAULT_GRANULARITY)))}


# ---- validation (replay with the rules) ----------------------------------------------------------
def _period_map(sc: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(p["period"]): p for p in sc["periods"]}


def validate_scenario(sc: dict[str, Any], ctx: GameContext) -> list[str]:
    """Return the list of problems (empty = valid)."""
    errs: list[str] = []
    names = list(ctx.names)
    sid = ctx.setup.setup_id
    if sc.get("setup_id") != sid:
        errs.append(f"setup_id {sc.get('setup_id')!r} != {sid!r}")
    gran = str(sc.get("granularity", DEFAULT_GRANULARITY))
    if gran not in GRANULARITIES:
        errs.append(f"granularity {gran!r} not in {GRANULARITIES}")
    seats = sc.get("seats") or {}
    for n in names:
        if not str(seats.get(n, "")).strip():
            errs.append(f"seats: no line for {n}")
    for n in seats:
        if n not in names:
            errs.append(f"seats: unknown name {n!r}")
    periods = sc.get("periods") or []
    nums = [int(p.get("period", -1)) for p in periods]
    if not periods:
        return errs + ["no periods"]
    for p in periods:
        if not str(p.get("public", "")).strip():
            errs.append(f"period {p.get('period')}: empty public text")
    first = int(ctx.rules["first_round"])
    if nums != list(range(first, first + len(nums))):
        errs.append(f"periods must be {first}, {first + 1}, ... without gaps; got {nums}")
        return errs
    final = sc.get("final") or {}
    if gran != "process":
        if ctx.domain == "aiwolf":
            errs += _validate_aiwolf(periods, final, ctx)
        else:
            errs += _validate_discussion(periods, final, ctx)
    elif any(k in p for p in periods for k in ("votes", "executed", "adopted", "attack", "divine")) or final:
        errs.append("a process plan must not carry outcome fields")
    if gran == "turn":
        errs += _validate_turns(periods, ctx)
    errs += _validate_prose(periods, seats, ctx)
    return errs


def _validate_prose(periods: list[dict[str, Any]], seats: dict[str, Any], ctx: GameContext | None = None) -> list[str]:
    """The public lines and the participants' lines describe the *process* (topics, criteria, how views move), never the
    outcome or a preference for a named target: no outcome / preference words, no option names, labels or distinctive
    option words (discussion domains: the options are revealed only in the last round), and in aiwolf no player named in
    the public lines (who is suspected or voted is the outcome). The turn lines are exempt (turn granularity is the upper
    bound and is only given to public conditions)."""
    errs: list[str] = []
    names = list(ctx.names) if ctx is not None else []
    opt_names: list[str] = []
    opt_words: set[str] = set()
    aiwolf = ctx is not None and ctx.domain == "aiwolf"
    if ctx is not None and not aiwolf:
        # distinctive option words = words of the option names that do not occur in the material the participants
        # already have (topic title / context, concerns, card texts); the others are ordinary topic vocabulary
        inst = ctx.instance or {}
        material = " ".join([str(inst.get("topic", {}).get("title", "")), str(inst.get("topic", {}).get("context", "")),
                             *[str(v) for v in (inst.get("problems") or {}).values()],
                             *[str(c.get("text", "")) + " " + str(c.get("title", "")) for c in ctx.card_pool()]]).lower()
        mat_words = set(re.findall(r"[a-z]{4,}", material))
        for o in ctx.options():
            opt_names.append(str(o["name"]))
            for w in re.findall(r"[A-Za-z]{4,}", str(o["name"])):
                if w.lower() not in mat_words:
                    opt_words.add(w.lower())
    name_re = re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b") if names else None

    def check(where: str, text: str, own: str | None = None) -> None:
        t = str(text)
        m = _OUTCOME_WORDS.search(t)
        if m:
            errs.append(f"{where}: states an outcome or a preference ({m.group(0)!r}); describe the process only")
        for on in opt_names:
            if on.lower() in t.lower():
                errs.append(f"{where}: names the option {on!r} (options are revealed only in the last round)")
        for w in sorted(opt_words):
            if re.search(r"\b" + re.escape(w) + r"\b", t, re.I):
                errs.append(f"{where}: uses the option word {w!r}")
        m = _LABEL_REF.search(t)
        if m and not aiwolf:
            errs.append(f"{where}: refers to an option by its label ({m.group(0)!r})")
        if aiwolf and name_re is not None:
            for mm in name_re.finditer(t):
                if mm.group(1) != own:
                    errs.append(f"{where}: names the player {mm.group(1)} (who is suspected or targeted is the outcome)")
                    break
        if aiwolf:
            m = _AIWOLF_ROLE_WORDS.search(t)
            if m:
                errs.append(f"{where}: mentions a role, claim or divination ({m.group(0)!r}); a process plan describes the flow of the talk only")

    for p in periods:
        check(f"period {p.get('period')} public", p.get("public", ""))
    for n, t in (seats or {}).items():
        check(f"seats[{n}]", t, own=n)
    return errs


def _validate_turns(periods: list[dict[str, Any]], ctx: GameContext) -> list[str]:
    """turn granularity: every period has ``turns`` = [{turn, lines{name: gist}}]; names valid and alive
    (aiwolf: not executed / attacked before), turn numbers 1..turns_per_round, a participant who said Over has
    no later line in that period."""
    errs: list[str] = []
    n_turns = int(ctx.rules["turns_per_round"])
    over_tok = str(ctx.rules["pass_over"])
    alive = list(ctx.names)
    for p in periods:
        n = int(p["period"])
        turns = p.get("turns")
        if not isinstance(turns, list) or not turns:
            errs.append(f"period {n}: turns missing (granularity turn)")
        else:
            seen: set[int] = set()
            over: set[str] = set()
            for t in turns:
                try:
                    tn = int(t.get("turn"))
                except (TypeError, ValueError):
                    errs.append(f"period {n}: a turn without a number")
                    continue
                if not 1 <= tn <= n_turns or tn in seen:
                    errs.append(f"period {n}: bad or repeated turn {tn}")
                seen.add(tn)
                lines = t.get("lines") or {}
                if not isinstance(lines, dict) or not lines:
                    errs.append(f"period {n} turn {tn}: no lines")
                    continue
                for name, gist in lines.items():
                    if name not in ctx.names:
                        errs.append(f"period {n} turn {tn}: unknown name {name!r}")
                    elif name not in alive:
                        errs.append(f"period {n} turn {tn}: {name} is dead")
                    elif name in over:
                        errs.append(f"period {n} turn {tn}: {name} already said {over_tok}")
                    if not str(gist).strip():
                        errs.append(f"period {n} turn {tn}: empty line for {name}")
                    if str(gist).strip() == over_tok:
                        over.add(name)
        if ctx.domain == "aiwolf":
            for k in ("executed", "attack"):
                v = p.get(k)
                if v in alive:
                    alive.remove(v)
    return errs


def _check_votes(p: dict[str, Any], voters: list[str], targets: list[str], sid: str, n: int,
                 key: str, errs: list[str]) -> str | None:
    votes = p.get("votes")
    if not isinstance(votes, dict) or not votes:
        errs.append(f"period {n}: votes missing")
        return None
    for v, t in votes.items():
        if v not in voters:
            errs.append(f"period {n}: {v!r} cannot vote (not alive / unknown)")
        if t not in targets:
            errs.append(f"period {n}: vote target {t!r} not allowed")
    missing = [v for v in voters if v not in votes]
    if missing:
        errs.append(f"period {n}: no vote for {missing}")
    t = tally({v: (x if x in targets else None) for v, x in votes.items()}, sid, n)
    planned = p.get(key)
    if planned != t.chosen:
        errs.append(f"period {n}: {key} {planned!r} does not follow from the votes (rule gives {t.chosen!r})")
    return t.chosen


def _validate_aiwolf(periods: list[dict[str, Any]], final: dict[str, Any], ctx: GameContext) -> list[str]:
    errs: list[str] = []
    sid = ctx.setup.setup_id
    role_of = {n: ctx.role_of_name(n) for n in ctx.names}
    alive = list(ctx.names)
    seer = next((n for n in ctx.names if role_of[n] == Role.SEER), None)
    wolf = next((n for n in ctx.names if role_of[n] == Role.WEREWOLF), None)
    winner: str | None = None

    def species(n: str) -> str:
        return str(Role(role_of[n]).species)

    def check_win() -> str | None:
        wolves = sum(1 for n in alive if species(n) == "WEREWOLF")
        humans = sum(1 for n in alive if species(n) == "HUMAN")
        if wolves == 0:
            return WINNER_VILLAGE
        if wolves >= humans:
            return WINNER_WEREWOLF
        return None

    for p in periods:
        n = int(p["period"])
        if winner is not None:
            errs.append(f"period {n}: the game was already decided ({winner})")
            break
        if n >= 1:
            chosen = _check_votes(p, alive, alive, sid, n, "executed", errs)
            if chosen and chosen in alive:
                alive.remove(chosen)
            winner = check_win()
            if winner is not None:
                for k in ("attack", "divine"):
                    if p.get(k) not in (None, ""):
                        errs.append(f"period {n}: no {k} after the deciding execution (the game is over)")
                continue
        d = p.get("divine")
        if seer in alive:
            if d in (None, ""):
                errs.append(f"period {n}: the Seer ({seer}) must divine someone")
            elif d not in alive or d == seer:
                errs.append(f"period {n}: divine target {d!r} not allowed")
        elif d not in (None, ""):
            errs.append(f"period {n}: the Seer is dead, no divination")
        if n >= 1:
            a = p.get("attack")
            if a in (None, ""):
                errs.append(f"period {n}: the Werewolf must attack someone")
            elif a not in alive or a == wolf:
                errs.append(f"period {n}: attack target {a!r} not allowed")
            else:
                alive.remove(a)
            winner = check_win()
    if winner is None:
        errs.append("the plan does not end the game (no side has won after the last period)")
    elif final.get("winner") != winner:
        errs.append(f"final.winner {final.get('winner')!r} != {winner!r} (from the plan)")
    return errs


def _validate_discussion(periods: list[dict[str, Any]], final: dict[str, Any], ctx: GameContext) -> list[str]:
    errs: list[str] = []
    last = int(ctx.rules["rounds_total"])
    labels = ctx.option_labels()
    nums = [int(p["period"]) for p in periods]
    if nums[-1] != last:
        errs.append(f"the last period must be {last}")
        return errs
    for p in periods:
        n = int(p["period"])
        if n == last:
            chosen = _check_votes(p, list(ctx.names), labels, ctx.setup.setup_id, n, "adopted", errs)
            if final.get("adopted") != chosen:
                errs.append(f"final.adopted {final.get('adopted')!r} != {chosen!r} (from the votes)")
        elif p.get("votes") or p.get("adopted"):
            errs.append(f"period {n}: votes only in the last period")
    return errs


# ---- mechanical repairs of a generated plan ------------------------------------------------------
def repair_plan(sc: dict[str, Any], ctx: GameContext) -> list[str]:
    """Deterministic fixes of errors a model keeps making, applied before validation (recorded by the generator):
    - turn lines of a participant who already said Over in that period are dropped;
    - night actions (divine / attack) in the period whose execution already ends the game are dropped, and so are
      any later periods (aiwolf);
    - turns numbered 0, 1, 2, ... (the model counting turns from 0 as it counts Day 0) are renumbered 1, 2, 3, ...
    Returns the list of repairs made."""
    done: list[str] = []
    over_tok = str(ctx.rules["pass_over"])
    for p in sc.get("periods") or []:
        n = p.get("period")
        over: set[str] = set()
        turns = p.get("turns") or []
        nums = [t.get("turn") for t in turns]
        if turns and all(isinstance(x, int) for x in nums) and nums == list(range(len(turns))):
            for t in turns:
                t["turn"] = int(t["turn"]) + 1
            done.append(f"period {n}: renumbered turns 0..{len(turns) - 1} to 1..{len(turns)}")
        for t in turns:
            lines = t.get("lines") or {}
            for name in list(lines):
                if name in over:
                    del lines[name]
                    done.append(f"period {n} turn {t.get('turn')}: dropped {name}'s line after {over_tok}")
                elif str(lines[name]).strip() == over_tok:
                    over.add(name)
        empty = [t for t in turns if not (t.get("lines") or {})]
        if empty and turns:
            p["turns"] = [t for t in turns if t.get("lines")]
            done.append(f"period {n}: dropped {len(empty)} empty turn(s)")
    if ctx.domain == "aiwolf":
        role_of = {n: ctx.role_of_name(n) for n in ctx.names}
        alive = list(ctx.names)

        def decided() -> bool:
            wolves = sum(1 for x in alive if str(Role(role_of[x]).species) == "WEREWOLF")
            humans = sum(1 for x in alive if str(Role(role_of[x]).species) == "HUMAN")
            return wolves == 0 or wolves >= humans

        for p in sc.get("periods") or []:
            n = p.get("period")
            ex = p.get("executed")
            if ex in alive:
                alive.remove(ex)
            if ex and decided():
                for k in ("divine", "attack"):
                    if p.get(k) not in (None, ""):
                        p[k] = None
                        done.append(f"period {n}: dropped {k} after the deciding execution")
                periods = sc.get("periods") or []
                idx = periods.index(p)
                if len(periods) > idx + 1:
                    sc["periods"] = periods[:idx + 1]
                    done.append(f"period {n}: dropped {len(periods) - idx - 1} period(s) after the deciding execution")
                break
            a = p.get("attack")
            if a in alive:
                alive.remove(a)
    return done


# ---- granularity views ---------------------------------------------------------------------------
def scenario_view(sc: dict[str, Any], granularity: str | None = None) -> dict[str, Any]:
    """The plan at ``granularity`` (default: the file's own), derived from the file by deletion only.
    A coarser view of a finer file; asking for a finer view than the file holds is an error."""
    import copy
    have = str(sc.get("granularity", DEFAULT_GRANULARITY))
    want = str(granularity or have)
    if want not in GRANULARITIES:
        raise ValueError(f"granularity {want!r} not in {GRANULARITIES}")
    if _RANK[want] > _RANK[have] or (want == "outcome" and have == "process") or (want == "process" and have == "outcome"):
        raise ValueError(f"the plan holds {have!r}; {want!r} cannot be derived from it")
    out = copy.deepcopy(sc)
    out["granularity"] = want
    out["file_granularity"] = have
    if want != "turn":
        for p in out["periods"]:
            p.pop("turns", None)
    if want == "outcome":
        for p in out["periods"]:
            p.pop("public", None)
        out["seats"] = {}
    if want == "process":
        for p in out["periods"]:
            for k in ("votes", "executed", "adopted", "attack", "divine"):
                p.pop(k, None)
        out["final"] = {}
    return out


# ---- rendering context for common/prompts/scenario.jinja ----------------------------------------
def _votes_text(votes: dict[str, str] | None) -> str:
    if not votes:
        return ""
    return "Votes: " + ", ".join(f"{v} -> {t}" for v, t in votes.items()) + "."


def scenario_context(sc: dict[str, Any], ctx: GameContext, seats: Iterable[int] | None = None) -> dict[str, Any]:
    """``plan_periods`` / ``plan_final`` / ``plan_seats`` for the template. ``seats`` None = all five."""
    aiwolf = ctx.domain == "aiwolf"
    noun = str(ctx.rules["option_noun"])
    gran = str(sc.get("granularity", DEFAULT_GRANULARITY))
    periods = []
    for p in sc["periods"]:
        n = int(p["period"])
        parts = [str(p["public"]).strip()] if p.get("public") else []
        vt = _votes_text(p.get("votes"))
        if vt:
            parts.append(vt)
        if aiwolf:
            if n >= 1 and "executed" in p:
                parts.append(f"Executed: {p['executed'] or 'no one'}.")
            night = []
            if p.get("divine"):
                night.append(f"the Seer divines {p['divine']}")
            if p.get("attack"):
                night.append(f"the Werewolf attacks {p['attack']}")
            if night:
                parts.append("Night: " + "; ".join(night) + ".")
        elif "adopted" in p:
            parts.append(f"Adopted: {p['adopted'] or 'none'}.")
        turns = []
        if gran == "turn":
            for t in p.get("turns") or []:
                lines = t.get("lines") or {}
                turns.append({"turn": int(t["turn"]),
                              "text": "; ".join(f"{name}: {str(g).strip()}" for name, g in lines.items())})
        periods.append({"period": n, "text": " ".join(parts), "turns": turns})
    final = sc.get("final") or {}
    if not final:
        final_text = ""
    elif aiwolf:
        w = str(final.get("winner", ""))
        final_text = "the village wins." if w == WINNER_VILLAGE else "the werewolf wins." if w == WINNER_WEREWOLF else w
    else:
        final_text = f"{noun} {final.get('adopted')} is selected."
    seat_names = [ctx.name_of_seat(s) for s in seats] if seats is not None else list(ctx.names)
    arcs = sc.get("seats") or {}
    plan_seats = [{"name": n, "text": str(arcs[n]).strip()} for n in seat_names if n in arcs]
    return {"plan_periods": periods, "plan_final": final_text, "plan_seats": plan_seats, "plan_granularity": gran}


# ---- deviations of a played game from the plan ---------------------------------------------------
def _dev(period: int | None, what: str, planned: Any, actual: Any, **more: Any) -> dict[str, Any]:
    d: dict[str, Any] = {"period": period, "what": what, "planned": planned, "actual": actual}
    d.update(more)
    return {"seq": None, "code": "scenario_deviation", "kind": DEVIATION, "detail": d}


def find_scenario_deviations(rows: Iterable[LogRow], ctx: GameContext, sc: dict[str, Any]) -> list[dict[str, Any]]:
    """Same function for both methods (rows from the common log)."""
    rows = list(rows)
    out: list[dict[str, Any]] = []
    plan = _period_map(sc)
    aiwolf = ctx.domain == "aiwolf"
    played = sorted({r.round for r in rows if r.type in ("talk", "pass", "vote", "action")})
    for n in played:
        p = plan.get(n)
        if p is None:
            out.append(_dev(n, "period", None, "played"))
            continue
        votes = {r.agent: r.target for r in rows if r.type == "vote" and r.round == n}
        for voter, t in (p.get("votes") or {}).items():
            if voter in votes and votes[voter] != t:
                out.append(_dev(n, "vote", t, votes[voter], voter=voter))
        if aiwolf:
            ex = next((r for r in rows if r.type == "action" and r.round == n and r.extra.get("action") == "execute"), None)
            if ex is not None and "executed" in p and (ex.target or None) != (p["executed"] or None):
                out.append(_dev(n, "execution", p["executed"], ex.target or None))
            at = next((r for r in rows if r.type == "action" and r.round == n and r.extra.get("action") == "attack"), None)
            if at is not None and p.get("attack") and (at.target or None) != p["attack"]:
                out.append(_dev(n, "attack", p["attack"], at.target or None))
            dv = next((r for r in rows if r.type == "action" and r.round == n and r.extra.get("action") == "divine"), None)
            if dv is not None and p.get("divine") and (dv.target or None) != p["divine"]:
                out.append(_dev(n, "divine", p["divine"], dv.target or None))
    for n, p in plan.items():
        if n not in played:
            out.append(_dev(n, "period", "planned", None))
    res = next((r for r in rows if r.type == "result"), None)
    final = sc.get("final") or {}
    if res is not None:
        key = "winner" if aiwolf else "adopted"
        if final.get(key) is not None and res.text != final.get(key):
            out.append(_dev(None, key, final.get(key), res.text))
    return out


__all__ = ["DEFAULT_GRANULARITY", "DEVIATION", "GRANULARITIES", "SCENARIOS", "find_scenario_deviations", "load_scenario",
           "repair_plan", "resolve_scenario", "scenario_context", "scenario_header", "scenario_path", "scenario_sha1",
           "scenario_view", "validate_scenario"]
