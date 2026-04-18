"""
actions/ — Action execution package for Numa.

Public API: import only what you need from here.
The rest of the codebase should only ever need handle_intent.
"""

from actions.registry import handle_intent, INTENT_MAP

__all__ = ["handle_intent", "INTENT_MAP"]
