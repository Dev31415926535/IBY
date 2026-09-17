import json
import os
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone


# Change these paths if necessary
DATASETS = {
    "dataset_a": Path("dataset_a"),
    "dataset_b": Path("dataset_b"),
}

OUTPUT_DIR = Path("version_1/outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def read_jsonl(path):
    """Read a JSONL file one line at a time."""
    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                print(f"Warning: invalid JSON in {path}, line {line_number}")


def get_nested(d, *keys, default=None):
    """Safely access nested dictionaries."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key)

    return d if d is not None else default


def extract_domain(url):
    if not isinstance(url, str) or not url:
        return None

    match = re.match(r"https?://([^/]+)", url)
    return match.group(1).lower() if match else None


def parse_time(timestamp):
    if not timestamp:
        return None

    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def analyze_events_file(path, session_id, chunk_id):
    stats = {
        "events": 0,
        "event_types": Counter(),
        "layers": Counter(),
        "apps": Counter(),
        "process_names": Counter(),
        "window_titles": Counter(),
        "browser_domains": Counter(),
        "browser_titles": Counter(),
        "extracted_text_events": 0,
        "clipboard_events": 0,
        "screenshot_events": 0,
        "keystroke_events": 0,
        "mouse_events": 0,
        "browser_events": 0,
        "system_events": 0,
        "first_timestamp": None,
        "last_timestamp": None,
        "invalid_timestamps": 0,
    }

    for event in read_jsonl(path):
        stats["events"] += 1

        event_type = event.get("event_type", "<missing>")
        layer = event.get("layer", "<missing>")

        stats["event_types"][event_type] += 1
        stats["layers"][layer] += 1

        if event_type == "clipboard_change":
            stats["clipboard_events"] += 1

        if event_type == "screenshot_smart":
            stats["screenshot_events"] += 1

        if event_type == "keystroke":
            stats["keystroke_events"] += 1

        if event_type.startswith("mouse_"):
            stats["mouse_events"] += 1

        if layer == "L3":
            stats["browser_events"] += 1

        if layer == "SYSTEM":
            stats["system_events"] += 1

        # Application information
        active_app = get_nested(
            event, "context", "active_app", "app_name"
        )
        process_name = get_nested(
            event, "context", "active_app", "process_name"
        )
        window_title = get_nested(
            event, "context", "active_app", "window_title"
        )

        if active_app:
            stats["apps"][active_app] += 1

        if process_name:
            stats["process_names"][process_name] += 1

        if window_title:
            stats["window_titles"][window_title] += 1

        # Browser information
        browser_url = get_nested(
            event, "context", "active_browser_tab", "url"
        )
        browser_title = get_nested(
            event, "context", "active_browser_tab", "title"
        )

        domain = extract_domain(browser_url)

        if domain:
            stats["browser_domains"][domain] += 1

        if browser_title:
            stats["browser_titles"][browser_title] += 1

        # Extracted text
        extracted_text = get_nested(
            event, "context", "extracted_text"
        )

        if extracted_text:
            stats["extracted_text_events"] += 1

        # Timestamps
        timestamp = parse_time(event.get("timestamp_iso"))

        if timestamp is None:
            stats["invalid_timestamps"] += 1
        else:
            if stats["first_timestamp"] is None:
                stats["first_timestamp"] = timestamp

            stats["last_timestamp"] = timestamp

    return stats


def analyze_dataset(dataset_name, dataset_path):
    print(f"\nAnalyzing {dataset_name}...")

    dataset_stats = {
        "dataset": dataset_name,
        "sessions": 0,
        "chunks": 0,
        "events": 0,
        "event_types": Counter(),
        "layers": Counter(),
        "apps": Counter(),
        "process_names": Counter(),
        "window_titles": Counter(),
        "browser_domains": Counter(),
        "browser_titles": Counter(),
        "session_summaries": [],
        "invalid_timestamps": 0,
    }

    session_dirs = sorted(
        p for p in dataset_path.iterdir()
        if p.is_dir() and p.name.startswith("ses_")
    )

    dataset_stats["sessions"] = len(session_dirs)

    for session_dir in session_dirs:
        print(f"  Session: {session_dir.name}")

        session_stats = {
            "session_id": session_dir.name,
            "chunks": 0,
            "events": 0,
            "event_types": Counter(),
            "layers": Counter(),
            "apps": Counter(),
            "process_names": Counter(),
            "window_titles": Counter(),
            "browser_domains": Counter(),
            "browser_titles": Counter(),
            "first_timestamp": None,
            "last_timestamp": None,
            "invalid_timestamps": 0,
        }

        chunk_dirs = sorted(
            p for p in session_dir.iterdir()
            if p.is_dir() and p.name.startswith("chunk_")
        )

        session_stats["chunks"] = len(chunk_dirs)
        dataset_stats["chunks"] += len(chunk_dirs)

        for chunk_dir in chunk_dirs:
            events_path = chunk_dir / "events.jsonl"

            if not events_path.exists():
                continue

            chunk_stats = analyze_events_file(
                events_path,
                session_dir.name,
                chunk_dir.name,
            )

            session_stats["events"] += chunk_stats["events"]
            dataset_stats["events"] += chunk_stats["events"]

            for key in [
                "event_types",
                "layers",
                "apps",
                "process_names",
                "window_titles",
                "browser_domains",
                "browser_titles",
            ]:
                session_stats[key].update(chunk_stats[key])
                dataset_stats[key].update(chunk_stats[key])

            if chunk_stats["first_timestamp"]:
                if (
                    session_stats["first_timestamp"] is None
                    or chunk_stats["first_timestamp"]
                    < session_stats["first_timestamp"]
                ):
                    session_stats["first_timestamp"] = (
                        chunk_stats["first_timestamp"]
                    )

            if chunk_stats["last_timestamp"]:
                if (
                    session_stats["last_timestamp"] is None
                    or chunk_stats["last_timestamp"]
                    > session_stats["last_timestamp"]
                ):
                    session_stats["last_timestamp"] = (
                        chunk_stats["last_timestamp"]
                    )

            session_stats["invalid_timestamps"] += (
                chunk_stats["invalid_timestamps"]
            )

        if (
            session_stats["first_timestamp"]
            and session_stats["last_timestamp"]
        ):
            duration = (
                session_stats["last_timestamp"]
                - session_stats["first_timestamp"]
            ).total_seconds()
        else:
            duration = None

        dataset_stats["invalid_timestamps"] += (
            session_stats["invalid_timestamps"]
        )

        dataset_stats["session_summaries"].append({
            "session_id": session_stats["session_id"],
            "chunks": session_stats["chunks"],
            "events": session_stats["events"],
            "first_timestamp": (
                session_stats["first_timestamp"].isoformat()
                if session_stats["first_timestamp"] else None
            ),
            "last_timestamp": (
                session_stats["last_timestamp"].isoformat()
                if session_stats["last_timestamp"] else None
            ),
            "duration_seconds": duration,
            "invalid_timestamps": session_stats["invalid_timestamps"],
        })

    return dataset_stats


def counter_to_dict(counter):
    return dict(counter.most_common())


def make_json_serializable(stats):
    result = dict(stats)

    for key in [
        "event_types",
        "layers",
        "apps",
        "process_names",
        "window_titles",
        "browser_domains",
        "browser_titles",
    ]:
        result[key] = counter_to_dict(stats[key])

    return result


def main():
    for dataset_name, dataset_path in DATASETS.items():
        if not dataset_path.exists():
            print(f"Skipping missing directory: {dataset_path}")
            continue

        stats = analyze_dataset(dataset_name, dataset_path)

        output_path = OUTPUT_DIR / f"{dataset_name}_inventory.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                make_json_serializable(stats),
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"\nSaved: {output_path}")
        print(f"Sessions: {stats['sessions']}")
        print(f"Chunks:   {stats['chunks']}")
        print(f"Events:   {stats['events']}")

        print("\nTop event types:")
        for name, count in stats["event_types"].most_common(15):
            print(f"  {name}: {count}")

        print("\nTop applications:")
        for name, count in stats["apps"].most_common(15):
            print(f"  {name}: {count}")

        print("\nTop browser domains:")
        for name, count in stats["browser_domains"].most_common(15):
            print(f"  {name}: {count}")


if __name__ == "__main__":
    main()