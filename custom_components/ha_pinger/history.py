"""Compact observed check results, retained for thirty days."""

RETENTION = 30 * 86400
LOG_LIMIT = 2000
SLOT_SECONDS = 300
SLOTS_PER_DAY = 288


def record(state, now, online):
    # One hex digit per five minutes: 1=online, 2=offline, 4=technical error.
    # Multiple observations in a slot are combined, so an outage stays visible.
    day = int(now // 86400) * 86400
    key = str(day)
    timeline = state.setdefault("timeline", {})
    cells = list(timeline.get(key, "0" * SLOTS_PER_DAY))
    index = int((now - day) // SLOT_SECONDS)
    cells[index] = format(int(cells[index], 16) | (1 if online is True else 2 if online is False else 4), "x")
    timeline[key] = "".join(cells)
    prune(state, now)


def prune(state, now):
    cutoff = now - RETENTION
    state["timeline"] = {day: cells for day, cells in state.get("timeline", {}).items()
                         if int(day) + 86400 > cutoff}
    state["log"] = [entry for entry in state.get("log", []) if entry["time"] >= cutoff][-LOG_LIMIT:]


def migrate(state, now):
    """Preserve the available legacy samples without inventing earlier uptime."""
    if "timeline" not in state:
        for point in state.get("history", []):
            if point["time"] >= now - RETENTION:
                record(state, point["time"], point["online"])
    prune(state, now)
