from pydantic import BaseModel, Field
from typing import Literal, Set, List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

timestamp=datetime.now(ZoneInfo("America/Los_Angeles"))

class Event(BaseModel):
    state: Literal['explore', 'combat', 'stealth'] = Field(..., description="Game context/state")
    intensity: int = Field(..., ge=0, le=100, description="Intensity 0-100")
    flags: Set[str] = Field(default_factory=set, description="Event flags (e.g., low_health, boss)")

class MusicalIntent(BaseModel):
    theme: Literal['explore', 'combat', 'stealth']
    active_stems: List[str]                   # List like ["pad", "bass", "drums"]
    target_gains: Dict[str, float]            # {"pad": 0.5, "drums": 1.0, ...}
    fade_durations: Dict[str, float]          # {"pad": 2.0, "drums": 1.0, ...} (seconds)
    timestamp: datetime

class SessionLogEntry(BaseModel):
    event: Event
    intent: MusicalIntent