from google.adk.agents import LoopAgent
from schemas import Event, MusicalIntent, SessionLogEntry
from datetime import datetime
from zoneinfo import ZoneInfo

# Subclass LoopAgent to implement your music planning logic
class MusicalDecisionAgent(LoopAgent):
    def act(self, ctx, event):
        # Choose stems by state
        if event.state == "explore":
            stems = ["pad", "bass"]
        elif event.state == "stealth":
            stems = ["pad", "fx"]
        elif event.state == "combat":
            stems = ["pad", "bass", "drums"]
        else:
            stems = ["pad"]

        # Flags can add stems or adjust behavior
        if "boss" in event.flags and event.state == "combat":
            if "fx" not in stems:
                stems.append("fx")

        # Gains scale with intensity; make 'fx' a bit more aggressive for boss
        gains = {}
        for stem in stems:
            if stem == "fx" and "boss" in event.flags:
                gains[stem] = min(event.intensity / 90, 1.0)
            else:
                gains[stem] = event.intensity / 100

        # Fades tuned by context
        if "boss" in event.flags:
            fade_val = 2.5
        elif event.intensity < 40:
            fade_val = 1.0
        else:
            fade_val = 1.5
        fades = {stem: fade_val for stem in stems}

        return MusicalIntent(
            theme=event.state,
            active_stems=stems,
            target_gains=gains,
            fade_durations=fades,
            timestamp=datetime.now(ZoneInfo("America/Los_Angeles"))
        )


class SessionLogger:
    def __init__(self):
        self.log = []
        # Instantiate your custom LoopAgent subclass
        self.agent = MusicalDecisionAgent(name="MusicalDecisionAgent")

    def post_event(self, event: Event):
        # Use LoopAgent for deterministic planning
        intent = self.agent.act(None, event)
        entry = SessionLogEntry(event=event, intent=intent)
        self.log.append(entry)
        return entry

    def to_json(self):
        # Serialize log for replay/export
        import json
        return json.dumps([entry.dict() for entry in self.log], indent=2, default=str)
