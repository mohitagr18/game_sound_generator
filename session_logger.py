from google.adk.agents import LoopAgent
from schemas import Event, MusicalIntent, SessionLogEntry
from datetime import datetime
from zoneinfo import ZoneInfo

# Subclass LoopAgent to implement your music planning logic
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import PrivateAttr


class MusicalDecisionAgent(LoopAgent):
    _last_switch_time: dict = PrivateAttr(default_factory=dict)
    _min_dwell: timedelta = PrivateAttr(default=timedelta(seconds=4))
    _min_fade: float = PrivateAttr(default=0.7)
    _max_fade: float = PrivateAttr(default=4.0)

    def act(self, ctx, event):
        now = datetime.now(ZoneInfo("America/Los_Angeles"))
        stems_by_state = {
            "explore": ["pad", "bass"],
            "stealth": ["pad", "fx"],
            "combat": ["pad", "bass", "drums"],
        }
        stems = stems_by_state.get(event.state, ["pad"])
        if "boss" in event.flags and event.state == "combat":
            if "fx" not in stems:
                stems.append("fx")

        agent_key = f"{event.state}:{'-'.join(sorted(event.flags))}"
        last_time = self._last_switch_time.get(agent_key)

        is_new_set = last_time is None or (now - last_time) >= self._min_dwell
        if is_new_set:
            self._last_switch_time[agent_key] = now

        gains = {}
        for stem in stems:
            if stem == "fx" and "boss" in event.flags:
                gains[stem] = min(event.intensity / 90, 1.0)
            else:
                gains[stem] = event.intensity / 100

        if "boss" in event.flags:
            fade_val = min(max(2.5, self._min_fade), self._max_fade)
        elif event.intensity < 40:
            fade_val = min(max(1.0, self._min_fade), self._max_fade)
        else:
            fade_val = min(max(1.5, self._min_fade), self._max_fade)
        fades = {stem: fade_val for stem in stems}

        return MusicalIntent(
            theme=event.state,
            active_stems=stems,
            target_gains=gains,
            fade_durations=fades,
            timestamp=now
        )


def serialize_entry(entry):
    # Converts SessionLogEntry (or any nested dict) to a dict, turning sets into lists for JSON
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, 'dict'):
            return clean(obj.dict())
        else:
            return obj
    return clean(entry)

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
        return json.dumps([serialize_entry(entry) for entry in self.log], indent=2, default=str)

    def replay_log(self, event_dicts):
        from schemas import Event, SessionLogEntry
        replayed = []
        for event_dict in event_dicts:
            event = Event(**event_dict)  # note: no 'event' key, just direct unpack!
            intent = self.agent.act(None, event)
            entry = SessionLogEntry(event=event, intent=intent)
            replayed.append(entry)
        return replayed


    def kpi_report(self):
        """Compute simple KPIs from session log."""
        from collections import Counter, defaultdict
        stem_counts = Counter()
        transitions = 0
        prev_state = None
        for entry in self.log:
            # Count stems
            stem_counts.update(entry.intent.active_stems)
            # Count transitions between states
            state = entry.event.state
            if prev_state is not None and state != prev_state:
                transitions += 1
            prev_state = state
        return {
            "total_events": len(self.log),
            "total_transitions": transitions,
            "most_active_stems": stem_counts.most_common(),
        }


