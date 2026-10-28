"""Wire protocol between server and agents.

Wire-compatible with aiwolf-nlp-common 0.7.0 (same request names, same JSON keys) so that
existing aiwolf agents can connect. Domain extensions (problem, card_titles, investigate_result,
options) are extra keys inside ``info`` that aiwolf-nlp-common simply ignores.

Transport: one JSON object per websocket text message (server -> agent); the agent replies with a
plain string (the utterance / the name / "Acknowledged.").
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Request(StrEnum):
    NAME = "NAME"
    INITIALIZE = "INITIALIZE"
    DAILY_INITIALIZE = "DAILY_INITIALIZE"
    TALK = "TALK"
    WHISPER = "WHISPER"
    VOTE = "VOTE"
    DIVINE = "DIVINE"
    GUARD = "GUARD"
    ATTACK = "ATTACK"
    INVESTIGATE = "INVESTIGATE"
    DAILY_FINISH = "DAILY_FINISH"
    FINISH = "FINISH"


ACTION_REQUESTS = (Request.DIVINE, Request.ATTACK, Request.INVESTIGATE)
NOTICE_REQUESTS = (Request.INITIALIZE, Request.DAILY_INITIALIZE, Request.DAILY_FINISH, Request.FINISH)


class Status(StrEnum):
    ALIVE = "ALIVE"
    DEAD = "DEAD"


class Role(StrEnum):
    WEREWOLF = "WEREWOLF"
    POSSESSED = "POSSESSED"
    SEER = "SEER"
    BODYGUARD = "BODYGUARD"
    VILLAGER = "VILLAGER"
    MEDIUM = "MEDIUM"
    PARTICIPANT = "PARTICIPANT"  # candidate_selection / shared_living

    @property
    def species(self) -> str:
        return Species.WEREWOLF if self == Role.WEREWOLF else Species.HUMAN

    @property
    def team(self) -> str:
        return Team.WEREWOLF if self in (Role.WEREWOLF, Role.POSSESSED) else Team.VILLAGER


class Species(StrEnum):
    HUMAN = "HUMAN"
    WEREWOLF = "WEREWOLF"


class Team(StrEnum):
    VILLAGER = "VILLAGER"
    WEREWOLF = "WEREWOLF"


# Pass tokens. Agents output exactly these strings; the server also accepts the Go server's
# FORCE_SKIP marker (used by agents on internal error).
T_SKIP = "Skip"
T_OVER = "Over"
T_FORCE_SKIP = "ForceSkip"
ACK = "Acknowledged."


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


@dataclass
class Talk:
    idx: int
    day: int
    turn: int
    agent: str
    text: str
    skip: bool = False
    over: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(o: dict[str, Any]) -> "Talk":
        return Talk(int(o["idx"]), int(o["day"]), int(o["turn"]), str(o["agent"]), str(o["text"]),
                    bool(o.get("skip", False)), bool(o.get("over", False)))


@dataclass
class Judge:
    day: int
    agent: str
    target: str
    result: str  # Species

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(o: dict[str, Any]) -> "Judge":
        return Judge(int(o["day"]), str(o["agent"]), str(o["target"]), str(o["result"]))


@dataclass
class Vote:
    day: int
    agent: str
    target: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(o: dict[str, Any]) -> "Vote":
        return Vote(int(o["day"]), str(o["agent"]), str(o["target"]))


@dataclass
class Info:
    game_id: str
    day: int
    agent: str
    status_map: dict[str, str]
    role_map: dict[str, str]
    profile: str | None = None
    medium_result: Judge | None = None
    divine_result: Judge | None = None
    executed_agent: str | None = None
    attacked_agent: str | None = None
    vote_list: list[Vote] | None = None
    attack_vote_list: list[Vote] | None = None
    remain_count: int | None = None
    remain_length: int | None = None
    remain_skip: int | None = None
    # --- domain extensions (candidate_selection / shared_living) ---
    problem: str | None = None                       # INITIALIZE: the seat's own concern
    card_titles: list[str] | None = None             # INITIALIZE (dynamic): titles that can be looked into
    investigate_result: list[dict[str, str]] | None = None  # DAILY_INITIALIZE round 2: [{card_id,title,text}]
    options: list[dict[str, str]] | None = None      # DAILY_INITIALIZE round 3: [{label,name,summary}]
    adopted: str | None = None                       # FINISH (discussion): the adopted label

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "game_id": self.game_id, "day": self.day, "agent": self.agent, "profile": self.profile,
            "medium_result": self.medium_result.to_dict() if self.medium_result else None,
            "divine_result": self.divine_result.to_dict() if self.divine_result else None,
            "executed_agent": self.executed_agent, "attacked_agent": self.attacked_agent,
            "vote_list": [v.to_dict() for v in self.vote_list] if self.vote_list is not None else None,
            "attack_vote_list": [v.to_dict() for v in self.attack_vote_list]
            if self.attack_vote_list is not None else None,
            "status_map": dict(self.status_map), "role_map": dict(self.role_map),
            "remain_count": self.remain_count, "remain_length": self.remain_length,
            "remain_skip": self.remain_skip,
            "problem": self.problem, "card_titles": self.card_titles,
            "investigate_result": self.investigate_result, "options": self.options, "adopted": self.adopted,
        }
        return _drop_none(d)

    @staticmethod
    def from_dict(o: dict[str, Any]) -> "Info":
        return Info(
            game_id=str(o.get("game_id")), day=int(o.get("day", 0)), agent=str(o.get("agent")),
            status_map={k: str(v) for k, v in (o.get("status_map") or {}).items()},
            role_map={k: str(v) for k, v in (o.get("role_map") or {}).items()},
            profile=o.get("profile"),
            medium_result=Judge.from_dict(o["medium_result"]) if o.get("medium_result") else None,
            divine_result=Judge.from_dict(o["divine_result"]) if o.get("divine_result") else None,
            executed_agent=o.get("executed_agent"), attacked_agent=o.get("attacked_agent"),
            vote_list=[Vote.from_dict(v) for v in o["vote_list"]] if o.get("vote_list") is not None else None,
            attack_vote_list=[Vote.from_dict(v) for v in o["attack_vote_list"]]
            if o.get("attack_vote_list") is not None else None,
            remain_count=o.get("remain_count"), remain_length=o.get("remain_length"),
            remain_skip=o.get("remain_skip"),
            problem=o.get("problem"), card_titles=o.get("card_titles"),
            investigate_result=o.get("investigate_result"), options=o.get("options"), adopted=o.get("adopted"),
        )


@dataclass
class Setting:
    """Game settings. Mirrors aiwolf-nlp-common Setting; stored as the nested dict it serialises to."""
    agent_count: int = 5
    max_day: int | None = 3
    role_num_map: dict[str, int] = field(default_factory=dict)
    vote_visibility: bool = True
    talk: dict[str, Any] = field(default_factory=lambda: {
        "max_count": {"per_agent": 4, "per_day": 20},
        "max_length": {"count_in_word": True, "count_spaces": False, "per_talk": None,
                       "mention_length": None, "per_agent": None, "base_length": None},
        "max_skip": 4})
    whisper: dict[str, Any] = field(default_factory=lambda: {
        "max_count": {"per_agent": 0, "per_day": 0},
        "max_length": {"count_in_word": True, "count_spaces": False, "per_talk": None,
                       "mention_length": None, "per_agent": None, "base_length": None},
        "max_skip": 0})
    vote: dict[str, Any] = field(default_factory=lambda: {"max_count": 1, "allow_self_vote": True})
    attack_vote: dict[str, Any] = field(default_factory=lambda: {
        "max_count": 1, "allow_self_vote": False, "allow_no_target": False})
    timeout: dict[str, Any] = field(default_factory=lambda: {"action": 600000, "response": 600000})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(o: dict[str, Any]) -> "Setting":
        s = Setting()
        for k in ("agent_count", "max_day", "role_num_map", "vote_visibility", "talk", "whisper",
                  "vote", "attack_vote", "timeout"):
            if k in o and o[k] is not None:
                setattr(s, k, o[k])
        return s


@dataclass
class Packet:
    request: Request
    info: Info | None = None
    setting: Setting | None = None
    talk_history: list[Talk] | None = None
    whisper_history: list[Talk] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": str(self.request),
            "info": self.info.to_dict() if self.info else None,
            "setting": self.setting.to_dict() if self.setting else None,
            "talk_history": [t.to_dict() for t in self.talk_history] if self.talk_history is not None else None,
            "whisper_history": [t.to_dict() for t in self.whisper_history]
            if self.whisper_history is not None else None,
        }

    @staticmethod
    def from_dict(o: dict[str, Any]) -> "Packet":
        return Packet(
            request=Request(str(o["request"])),
            info=Info.from_dict(o["info"]) if o.get("info") else None,
            setting=Setting.from_dict(o["setting"]) if o.get("setting") else None,
            talk_history=[Talk.from_dict(t) for t in o["talk_history"]] if o.get("talk_history") is not None else None,
            whisper_history=[Talk.from_dict(t) for t in o["whisper_history"]]
            if o.get("whisper_history") is not None else None,
        )
