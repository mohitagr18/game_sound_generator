from pydantic import BaseModel, Field
from typing import Literal, Set, List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))

class Event(BaseModel):
    state: Literal['explore', 'combat', 'stealth', 'bosscombat'] = Field(..., description="Game context/state")
    intensity: int = Field(..., ge=0, le=100, description="Intensity 0-100")
    flags: Set[str] = Field(default_factory=set, description="Event flags (e.g., low_health, boss)")

class MusicalIntent(BaseModel):
    theme: Literal['explore', 'combat', 'stealth', 'bosscombat']
    active_stems: List[str]
    target_gains: Dict[str, float]
    fade_durations: Dict[str, float]
    timestamp: datetime

class StemIntent(BaseModel):
    stem_name: str
    file_path: str
    target_gain: float
    fade_duration: float

class MixIntent(BaseModel):
    theme: Literal['explore', 'combat', 'stealth', 'bosscombat']
    stem_intents: List[StemIntent]

    def to_dict(self):
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
    event: Event
    intent: MusicalIntent
