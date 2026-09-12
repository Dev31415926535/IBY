import json
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter, defaultdict


DATASET = Path("dataset_a")
OUTPUT_FILE = Path("route_analysis.txt")


def get_url(event):
    payload = event.get("payload") or {}

    if not isinstance(payload, dict):
        return None

    for key in ["url", "target_url", "href"]:
        value = payload.get(key)

        if value:
            return value

    return None


def get_route(event):
    url = get_url(event)

    if not url:
        return None

    try:
        parsed = urlparse(url)

        # Example:
        # http://127.0.0.1:5122/#/onboarding
        if parsed.fragment:
            return parsed.fragment

        return parsed.path

    except Exception:
        return None


def load_events(session_dir):
    events = []

    for f in sorted(session_dir.rglob("events.jsonl")):

        try:
            with f.open("r", encoding="utf-8") as file:

                for line in file:
                    line = line.strip()

                    if not line:
                        continue

                    try:
                        event = json.loads(line)

                        if isinstance(event, dict):
                            events.append(event)

                    except json.JSONDecodeError:
                        continue

        except OSError:
            continue

    events.sort(
        key=lambda x: x.get("timestamp_ms", 0)
    )

    return events


# ---------------------------------------------------------
# Analyze routes
# ---------------------------------------------------------

route_transitions = Counter()
session_routes = defaultdict(list)


for session_dir in sorted(DATASET.iterdir()):

    if not session_dir.is_dir():
        continue

    events = load_events(session_dir)

    previous_route = None

    for event in events:

        if event.get("event_type") != "browser_navigation":
            continue

        route = get_route(event)

        if route is None:
            continue

        # Normalize route
        if route.startswith("#"):
            route = route[1:]

        if route == "":
            continue

        # Only record route when it changes
        if route != previous_route:

            session_routes[session_dir.name].append(route)

            if previous_route is not None:
                route_transitions[
                    (previous_route, route)
                ] += 1

            previous_route = route


# ---------------------------------------------------------
# Write results to TXT file
# ---------------------------------------------------------

with OUTPUT_FILE.open("w", encoding="utf-8") as output:

    # =====================================================
    # ROUTE TRANSITIONS
    # =====================================================

    output.write("\n")
    output.write("ROUTE TRANSITIONS\n")
    output.write("=" * 70)
    output.write("\n")

    if route_transitions:

        for (a, b), count in route_transitions.most_common():

            output.write(
                f"{count:5}  {a}  ->  {b}\n"
            )

    else:
        output.write("No route transitions found.\n")


    # =====================================================
    # SESSION ROUTE SEQUENCES
    # =====================================================

    output.write("\n")
    output.write("SESSION ROUTE SEQUENCES\n")
    output.write("=" * 70)
    output.write("\n")

    if session_routes:

        for session, routes in session_routes.items():

            output.write(f"\n{session}\n")

            for i, route in enumerate(routes, start=1):

                output.write(
                    f"  {i:2}. {route}\n"
                )

    else:
        output.write("No session routes found.\n")


# ---------------------------------------------------------
# Confirmation
# ---------------------------------------------------------

print(
    f"Route analysis written to: "
    f"{OUTPUT_FILE.resolve()}"
)
