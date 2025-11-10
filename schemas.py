# ---------------------------------------------------------------------------
# schemas.py
#
# Step-by-step overview:
# 1. Import required modules for type schemas, data validation
# 2. Define timestamp for current time (not used in classes themselves)
# 3. Define all core data classes (Event, MusicalIntent, StemIntent, MixIntent, SessionLogEntry)
#    using pydantic for validation and serialization.
# 4. Each class matches core app concepts: state event, mix configuration,
#    stem detail, session history.
# 5. Adds helper .to_dict for MixIntent to assist with explicit dict serialization
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import Literal, Set, List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

# Current timestamp in local (Pacific) timezone, used for logging/intent
timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))

class Event(BaseModel):
    """
    Represents a game event/state, with context (explore, combat, etc),
    intensity (0-100), and arbitrary flags (such as boss, low_health).
    """
    state: Literal['explore', 'combat', 'stealth', 'bosscombat'] = Field(..., description="Game context/state")
    intensity: int = Field(..., ge=0, le=100, description="Intensity 0-100")
    flags: Set[str] = Field(default_factory=set, description="Event flags (e.g., low_health, boss)")

class MusicalIntent(BaseModel):
    """
    Describes the musical configuration for a given theme:
    - Theme label, active stems, gains, fades, timestamp.
    """
    theme: Literal['explore', 'combat', 'stealth', 'bosscombat']
    active_stems: List[str]
    target_gains: Dict[str, float]
    fade_durations: Dict[str, float]
    timestamp: datetime

class StemIntent(BaseModel):
    """
    Details for a single stem (audio track) in a mix:
    - Name, path, target gain, fade duration.
    """
    stem_name: str
    file_path: str
    target_gain: float
    fade_duration: float

class MixIntent(BaseModel):
    """
    Bundles a group of StemIntents for a whole mix/theme.
    Provides a to_dict helper for easy serialization.
    """
    theme: Literal['explore', 'combat', 'stealth', 'bosscombat']
    stem_intents: List[StemIntent]

    def to_dict(self):
        """
        Convert MixIntent object to a nested dictionary, for JSON export or logging.
        """
        return {
            'theme': self.theme,
            'stems': [
                {
                    'stem_name': si.stem_name,
                    'file_path': si.file_path,
                    'target_gain': si.target_gain,
                    'fade_duration': si.fade_duration
                }
                for si in self.stem_intents
            ]
        }

class SessionLogEntry(BaseModel):
    """
    Represents a single entry in the session log: links an Event with its MusicalIntent.
    """
    event: Event
    intent: MusicalIntent
