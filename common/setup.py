"""Loading of data/ (personas, roles, rules, instances) and setups/ (one fixed game setup). DESIGN §4."""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import DOMAINS, ROOT

DATA = ROOT / "data"
SETUPS = ROOT / "setups"
CONFIG = ROOT / "config"
N_SEATS = 5
SEAT_NAMES = tuple(f"seat{i}" for i in range(1, N_SEATS + 1))  # connection names, sorted = seat order


@dataclass(frozen=True)
class Persona:
    name: str
    age: int
    gender: str
    personality: str


@dataclass
class Seat:
    seat: int
    persona: str
    role_slot: str


@dataclass
class Setup:
    setup_id: str
    domain: str
    k: int
    seats: list[Seat]
    speaking_order: list[int]
    info_mode: str = "dynamic"
    instance_id: str | None = None
    experiment_seed: int | None = None
    # discussion domains: the instance's option labels in the order they are shown, relabelled A, B, C, ... in that
    # order (counterbalancing of the label order across setups, audit 2026-10-28 E). None = the instance's order.
    option_perm: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(o: dict[str, Any]) -> "Setup":
        return Setup(setup_id=o["setup_id"], domain=o["domain"], k=int(o["k"]),
                     seats=[Seat(int(s["seat"]), s["persona"], s["role_slot"]) for s in o["seats"]],
                     speaking_order=[int(x) for x in o["speaking_order"]],
                     info_mode=o.get("info_mode", "dynamic"), instance_id=o.get("instance_id"),
                     experiment_seed=o.get("experiment_seed"),
                     option_perm=[str(x) for x in o["option_perm"]] if o.get("option_perm") else None)


# ---- loaders -----------------------------------------------------------------------------
def load_personas() -> dict[str, Persona]:
    d = yaml.safe_load((DATA / "personas.yml").read_text(encoding="utf-8"))
    out = {}
    for p in d["personas"]:
        out[p["name"]] = Persona(p["name"], int(p["age"]), str(p["gender"]), str(p["personality"]).strip())
    if len(out) != 24:
        raise ValueError(f"expected 24 personas, got {len(out)}")
    return out


def load_roles(domain: str) -> dict[str, Any]:
    _check_domain(domain)
    d = yaml.safe_load((DATA / domain / "roles.yml").read_text(encoding="utf-8"))
    slots = d["slots"]
    if sum(int(s["count"]) for s in slots.values()) != N_SEATS:
        raise ValueError(f"{domain}: role slot counts must sum to {N_SEATS}")
    return slots


def load_rules(domain: str) -> dict[str, Any]:
    _check_domain(domain)
    return yaml.safe_load((DATA / domain / "rules.yml").read_text(encoding="utf-8"))


def load_instances(domain: str) -> dict[str, dict[str, Any]]:
    _check_domain(domain)
    p = DATA / domain / "instances.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    return {inst["instance_id"]: inst for inst in d["instances"]}


def load_experiment() -> dict[str, Any]:
    return yaml.safe_load((CONFIG / "experiment.yml").read_text(encoding="utf-8"))


def load_models() -> dict[str, Any]:
    return yaml.safe_load((CONFIG / "models.yml").read_text(encoding="utf-8"))


def setup_path(domain: str, setup_id: str) -> Path:
    return SETUPS / domain / f"{setup_id}.json"


def resolve_setup_path(path_or_id: str | Path, domain: str | None = None) -> Path:
    """The setup JSON file for a path or a setup_id (``setups/<domain>/<id>.json``)."""
    p = Path(path_or_id)
    if not p.exists():
        if domain is None:
            domain = str(path_or_id).rsplit("_", 1)[0]
        p = setup_path(domain, str(path_or_id))
    return p


def load_setup(path_or_id: str | Path, domain: str | None = None) -> Setup:
    p = resolve_setup_path(path_or_id, domain)
    s = Setup.from_dict(json.loads(p.read_text(encoding="utf-8")))
    validate_setup(s)
    return s


def save_setup(s: Setup) -> Path:
    validate_setup(s)
    p = setup_path(s.domain, s.setup_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(s.to_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


def _check_domain(domain: str) -> None:
    if domain not in DOMAINS:
        raise ValueError(f"unknown domain {domain!r}; expected one of {DOMAINS}")


def validate_setup(s: Setup, personas: dict[str, Persona] | None = None,
                   roles: dict[str, Any] | None = None, instances: dict[str, Any] | None = None) -> None:
    _check_domain(s.domain)
    if s.setup_id != f"{s.domain}_{s.k:04d}":
        raise ValueError(f"setup_id {s.setup_id!r} does not match domain/k")
    if [x.seat for x in s.seats] != list(range(1, N_SEATS + 1)):
        raise ValueError("seats must be 1..5 in order")
    if sorted(s.speaking_order) != list(range(1, N_SEATS + 1)):
        raise ValueError("speaking_order must be a permutation of 1..5")
    if len({x.persona for x in s.seats}) != N_SEATS:
        raise ValueError("personas must be distinct")
    if s.info_mode not in ("dynamic", "fixed"):
        raise ValueError("info_mode must be dynamic or fixed")
    personas = personas if personas is not None else load_personas()
    roles = roles if roles is not None else load_roles(s.domain)
    for x in s.seats:
        if x.persona not in personas:
            raise ValueError(f"unknown persona {x.persona!r}")
        if x.role_slot not in roles:
            raise ValueError(f"unknown role slot {x.role_slot!r} for {s.domain}")
    from collections import Counter
    c = Counter(x.role_slot for x in s.seats)
    for slot, spec in roles.items():
        if c.get(slot, 0) != int(spec["count"]):
            raise ValueError(f"slot {slot}: expected {spec['count']}, got {c.get(slot, 0)}")
    if s.domain != "aiwolf":
        instances = instances if instances is not None else load_instances(s.domain)
        if s.instance_id not in instances:
            raise ValueError(f"unknown instance {s.instance_id!r}")
    elif s.instance_id is not None:
        raise ValueError("aiwolf setups have no instance_id")


# ---- generation (DESIGN §4.4) --------------------------------------------------------------
def option_permutation(domain: str, k: int, experiment_seed: int, instance: dict[str, Any]) -> list[str]:
    """The display order of the instance's options for setup k (its own seeded stream, so adding it to existing
    setups does not change their cast / roles / speaking order)."""
    labels = [str(o["label"]) for o in instance["topic"]["options"]]
    rng = random.Random(f"{experiment_seed}:{domain}:{k}:options")
    rng.shuffle(labels)
    return labels


def game_setup(domain: str, k: int, experiment_seed: int, info_mode: str = "dynamic",
               personas: dict[str, Persona] | None = None, roles: dict[str, Any] | None = None,
               instances: dict[str, Any] | None = None) -> Setup:
    _check_domain(domain)
    personas = personas if personas is not None else load_personas()
    roles = roles if roles is not None else load_roles(domain)
    rng = random.Random(f"{experiment_seed}:{domain}:{k}")
    cast = rng.sample(sorted(personas), N_SEATS)
    slot_list = sorted(slot for slot, spec in roles.items() for _ in range(int(spec["count"])))
    rng.shuffle(slot_list)
    order = list(range(1, N_SEATS + 1))
    rng.shuffle(order)
    instance_id = None
    option_perm = None
    if domain != "aiwolf":
        instances = instances if instances is not None else load_instances(domain)
        ids = sorted(instances)
        instance_id = ids[k % len(ids)]
        option_perm = option_permutation(domain, k, experiment_seed, instances[instance_id])
    s = Setup(setup_id=f"{domain}_{k:04d}", domain=domain, k=k,
              seats=[Seat(i + 1, cast[i], slot_list[i]) for i in range(N_SEATS)],
              speaking_order=order, info_mode=info_mode, instance_id=instance_id,
              experiment_seed=experiment_seed, option_perm=option_perm)
    validate_setup(s, personas, roles, instances)
    return s


# ---- bundle used by server / agent / single ------------------------------------------------
@dataclass
class GameContext:
    setup: Setup
    personas: dict[str, Persona]
    roles: dict[str, Any]
    rules: dict[str, Any]
    instance: dict[str, Any] | None = None
    _by_name: dict[str, Seat] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._by_name = {s.persona: s for s in self.setup.seats}

    @staticmethod
    def load(setup: Setup | str | Path) -> "GameContext":
        s = setup if isinstance(setup, Setup) else load_setup(setup)
        inst = load_instances(s.domain).get(s.instance_id) if s.instance_id else None
        return GameContext(s, load_personas(), load_roles(s.domain), load_rules(s.domain), inst)

    # ---- provenance of the setup file (jsonl header: setup_path / setup_sha1) ----------------
    def setup_file(self) -> Path | None:
        p = setup_path(self.domain, self.setup.setup_id)
        return p if p.is_file() else None

    def setup_path_str(self) -> str | None:
        """Path of the setup file, relative to the repository root when inside it."""
        p = self.setup_file()
        if p is None:
            return None
        try:
            return str(p.resolve().relative_to(ROOT.resolve()))
        except ValueError:
            return str(p)

    def setup_sha1(self) -> str | None:
        """sha1 of the setup JSON file bytes (None when the setup was not loaded from a file)."""
        p = self.setup_file()
        if p is None:
            return None
        import hashlib
        return hashlib.sha1(p.read_bytes()).hexdigest()

    @property
    def domain(self) -> str:
        return self.setup.domain

    @property
    def names(self) -> list[str]:
        """Names in seat order 1..5."""
        return [s.persona for s in self.setup.seats]

    @property
    def speaking_order_names(self) -> list[str]:
        return [self.name_of_seat(i) for i in self.setup.speaking_order]

    def name_of_seat(self, seat: int) -> str:
        return self.setup.seats[seat - 1].persona

    def seat_of_name(self, name: str) -> int:
        return self._by_name[name].seat

    def role_of_seat(self, seat: int) -> str:
        return self.setup.seats[seat - 1].role_slot

    def role_of_name(self, name: str) -> str:
        return self._by_name[name].role_slot

    def persona_of_name(self, name: str) -> Persona:
        return self.personas[name]

    def problem_of_seat(self, seat: int) -> str | None:
        if self.instance is None:
            return None
        return self.instance["problems"][str(seat)]

    def card_pool(self) -> list[dict[str, Any]]:
        return list(self.instance["card_pool"]) if self.instance else []

    def card_by_title(self, title: str) -> dict[str, Any] | None:
        t = title.strip().lower()
        for c in self.card_pool():
            if c["title"].strip().lower() == t:
                return c
        return None

    def card_by_id(self, card_id: str) -> dict[str, Any] | None:
        for c in self.card_pool():
            if c["card_id"] == card_id:
                return c
        return None

    def options(self) -> list[dict[str, str]]:
        """The options as shown in this setup: in ``setup.option_perm`` order, relabelled A, B, C, ... (the
        instance's own label is kept as ``orig_label``). Everything downstream (votes, plans, logs) uses the
        shown labels; the header records the permutation."""
        if not self.instance:
            return []
        opts = list(self.instance["topic"]["options"])
        perm = self.setup.option_perm
        if not perm:
            return [dict(o, orig_label=o["label"]) for o in opts]
        by_label = {str(o["label"]): o for o in opts}
        out = []
        for i, orig in enumerate(perm):
            o = by_label[orig]
            out.append(dict(o, label=chr(ord("A") + i), orig_label=str(o["label"])))
        return out

    def option_labels(self) -> list[str]:
        return [o["label"] for o in self.options()]

    def fixed_cards_of_seat(self, seat: int) -> list[dict[str, Any]]:
        ids = self.instance["fixed_assignment"][str(seat)]
        return [self.card_by_id(i) for i in ids]

    def check_dynamic_ready(self) -> None:
        if self.domain != "aiwolf" and self.setup.info_mode == "dynamic":
            missing = [c["card_id"] for c in self.card_pool() if not c.get("title")]
            if missing:
                raise ValueError(f"info_mode=dynamic needs card titles; missing for {missing} "
                                 f"in {self.setup.instance_id} (DESIGN §9-9)")
            titles = [c["title"] for c in self.card_pool()]
            if len({t.lower() for t in titles}) != len(titles):
                raise ValueError("card titles must be unique (case-insensitive)")
            for t in titles:
                if ";" in t or "\n" in t:
                    raise ValueError(f"card title must not contain ';' or newline: {t!r}")
