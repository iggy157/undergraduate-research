"""candidate_selection domain (source: panel). The logic is shared with shared_living."""
from .logic import DiscussionLogic


class CandidateSelectionLogic(DiscussionLogic):
    pass


__all__ = ["CandidateSelectionLogic", "DiscussionLogic"]
