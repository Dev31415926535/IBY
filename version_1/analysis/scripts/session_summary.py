import json
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse


DATASET = Path("dataset_a")
OUTPUT_FILE = Path("version_1/outputs/session_summary.txt")


def extract_domain(event):
    payload = event.get("payload") or {}

    if not isinstance(payload, dict):
        return None

    url = (
        payload.get("url")
        or payload.get("target_url")
        or payload.get("href")
        or ""
    )

    if not isinstance(url, str) or not url:
        return None

    try:
        parsed = urlparse(url)
        return parsed.netloc or None
    except Exception:
        return None


def extract_app_name(active_app):
    """
    Convert active_app into a string so it can
    safely be used as a Counter key.
    """

    if isinstance(active_app, str):
        return active_app.strip() or None

    if isinstance(active_app, dict):
        app_name = (
            active_app.get("name")
            or active_app.get("app_name")
            or active_app.get("app")
            or active_app.get("application")
            or active_app.get("process_name")
            or active_app.get("process")
        )

        if isinstance(app_name, str):
            return app_name.strip() or None

        return str(active_app)

    if active_app is not None:
        return str(active_app).strip() or None

    return None


# Open output file
with OUTPUT_FILE.open("w", encoding="utf-8") as output:

    for session_dir in sorted(DATASET.iterdir()):

        if not session_dir.is_dir():
            continue

        events = []

        # Find all events.jsonl files
        for events_file in sorted(session_dir.rglob("events.jsonl")):

            try:
                with events_file.open("r", encoding="utf-8") as f:

                    for line in f:
                        line = line.strip()

                        if not line:
                            continue

                        try:
                            event = json.loads(line)

                            if isinstance(event, dict):
                                events.append(event)

                        except json.JSONDecodeError:
                            pass

            except OSError as e:
                output.write(
                    f"Could not read {events_file}: {e}\n"
                )

        if not events:
            continue

        # Sort events chronologically
        events.sort(
            key=lambda e: e.get("timestamp_ms", 0)
        )

        # Count event types
        event_types = Counter(
            e.get("event_type", "UNKNOWN")
            for e in events
        )

        apps = Counter()
        domains = Counter()
        window_titles = Counter()

        # Process events
        for event in events:

            context = event.get("context") or {}

            if not isinstance(context, dict):
                context = {}

            # -------------------------------------------------
            # Application
            # -------------------------------------------------
            active_app = context.get("active_app")

            app_name = extract_app_name(active_app)

            if app_name:
                apps[app_name] += 1

            # -------------------------------------------------
            # Window title
            # -------------------------------------------------
            title = context.get("active_window_title")

            if isinstance(title, str) and title.strip():
                window_titles[title.strip()] += 1

            elif title is not None:
                window_titles[str(title)] += 1

            # -------------------------------------------------
            # Browser domain
            # -------------------------------------------------
            domain = extract_domain(event)

            if domain:
                domains[domain] += 1

        # -----------------------------------------------------
        # Calculate duration
        # -----------------------------------------------------
        start_ms = events[0].get("timestamp_ms")
        end_ms = events[-1].get("timestamp_ms")

        duration_minutes = None

        if (
            isinstance(start_ms, (int, float))
            and isinstance(end_ms, (int, float))
        ):
            duration_minutes = (
                end_ms - start_ms
            ) / 60000

        # =====================================================
        # WRITE SESSION SUMMARY
        # =====================================================

        output.write("\n" + "=" * 80 + "\n")
        output.write(f"{session_dir.name}\n")
        output.write("=" * 80 + "\n")

        output.write(f"Events: {len(events)}\n")

        if duration_minutes is not None:
            output.write(
                f"Duration: {duration_minutes:.2f} minutes\n"
            )
        else:
            output.write("Duration: unknown\n")

        # -----------------------------------------------------
        # Applications
        # -----------------------------------------------------
        output.write("\nApplications:\n")

        if apps:
            for name, count in apps.most_common(10):
                output.write(
                    f"  {count:6} {name}\n"
                )
        else:
            output.write(
                "  No application data found\n"
            )

        # -----------------------------------------------------
        # Browser domains
        # -----------------------------------------------------
        output.write("\nBrowser domains:\n")

        if domains:
            for name, count in domains.most_common(10):
                output.write(
                    f"  {count:6} {name}\n"
                )
        else:
            output.write(
                "  No browser domain data found\n"
            )

        # -----------------------------------------------------
        # Window titles
        # -----------------------------------------------------
        output.write("\nWindow titles:\n")

        if window_titles:
            for name, count in window_titles.most_common(10):
                output.write(
                    f"  {count:6} {name}\n"
                )
        else:
            output.write(
                "  No window title data found\n"
            )

        # -----------------------------------------------------
        # Event types
        # -----------------------------------------------------
        output.write("\nEvent types:\n")

        if event_types:
            for name, count in event_types.most_common(12):
                output.write(
                    f"  {count:6} {name}\n"
                )
        else:
            output.write(
                "  No event type data found\n"
            )

        output.write("\n")


print(f"Session summary written to: {OUTPUT_FILE.resolve()}")
