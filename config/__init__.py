"""
config/ — Configuration package for Numa.

Public API:
    from config.settings import settings

    settings.get("tts_voice")
    settings.set("tts_voice", "en-GB-SoniaNeural")
    settings.reload()
    settings.reset_to_defaults()
"""

from config.settings import settings

__all__ = ["settings"]
