import json
from typing import List
from schemas import Event, MusicalIntent, SessionLogEntry
from datetime import datetime
from zoneinfo import ZoneInfo

class SessionLogger:
    def __init__(self):
        self.log: List[SessionLogEntry] = []

    def post_event(self, event: Event):
        # Stub: replace with LoopAgent in Phase 1 main logic
        intent = MusicalIntent(
            theme=event.state,
            active_stems=["pad", "bass", "drums"],           # Stub stems
            target_gains={stem: event.intensity/100 for stem in ["pad", "bass", "drums"]},
            fade_durations={stem: 1.0 for stem in ["pad", "bass", "drums"]},
            timestamp=datetime.now(ZoneInfo("America/Los_Angeles"))
        )
        entry = SessionLogEntry(event=event, intent=intent)
        self.log.append(entry)
        return entry

    def to_json(self):
        # Serialize log for replay/export
        return json.dumps([entry.dict() for entry in self.log], indent=2, default=str)
