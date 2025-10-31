from pydantic import BaseModel, Field
from typing import Literal, Set, List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))

# Core game event model
class Event(BaseModel):
    state: Literal['explore', 'combat', 'stealth'] = Field(..., description="Game context/state")
    intensity: int = Field(..., ge=0, le=100, description="Intensity 0-100")
    flags: Set[str] = Field(default_factory=set, description="Event flags (e.g., low_health, boss)")

# Original intent for theme (MP3 file/simple mix)
class MusicalIntent(BaseModel):
    theme: Literal['explore', 'combat', 'stealth']
    active_stems: List[str]                # ["pad", "bass", "drums"]
    target_gains: Dict[str, float]         # {"pad": 0.5, "drums": 1.0}
    fade_durations: Dict[str, float]       # {"pad": 2.0, "drums": 1.0} in seconds
    timestamp: datetime

# Dynamic stem mixing intent model
class StemIntent(BaseModel):
    stem_name: str                        # "drums"
    file_path: str                        # "audioclips/explore/drums.wav"
    target_gain: float                    # 0.0 to 1.0
    fade_duration: float                  # seconds

class MixIntent(BaseModel):
    theme: Literal['explore', 'combat', 'stealth']
    stem_intents: List[StemIntent]        # List of StemIntent objects

    def to_dict(self):
        # For frontend serialization
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

# Log of intent/application events
class SessionLogEntry(BaseModel):
    event: Event
    intent: MusicalIntent
