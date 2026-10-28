"""shared_living domain (source: living). Same logic as candidate_selection; only instances differ."""
from server.candidate_selection.logic import DiscussionLogic


class SharedLivingLogic(DiscussionLogic):
    pass


__all__ = ["SharedLivingLogic"]
