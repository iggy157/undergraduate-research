"""Game server: runs one 5-seat game over websockets for any domain and writes the common log.

Entry points: ``python -m server`` (CLI, IMPLEMENTATION_NOTES §3) and ``server.base.runner.run_game``
(in-process, used by the tests).
"""
