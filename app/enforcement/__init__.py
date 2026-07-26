"""
Enforcement Package
-------------------
- Owns everything related to detecting and killing blocked processes.
- Runs independently of the UI (background thread) so blocking survives UI close.
- Modules: blocker (poll loop + kill logic), game_detection (heuristics for categorizing processes).
"""
