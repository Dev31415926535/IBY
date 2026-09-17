import json
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter, defaultdict
from datetime import datetime

DATASET = Path("dataset_a")
OUTPUT_FILE = Path("version_1/outputs/route_actions.txt")

def get_url(event):
    payload = event.get("payload")
    if not payload: payload = {}
    for key in ["url", "target_url", "href"]:
        value = payload.get(key)
        if value: return value
    ctx = event.get("context")
    if not ctx: ctx = {}
    context_url = ctx.get("active_browser_tab", {}).get("url") if isinstance(ctx.get("active_browser_tab"), dict) else None
    if context_url: return context_url
    return None

def get_route(event):
    url = get_url(event)
    if not url: return None
    try:
        parsed = urlparse(url)
        if parsed.fragment: return parsed.fragment
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
                    if not line: continue
                    try:
                        event = json.loads(line)
                        if isinstance(event, dict):
                            events.append(event)
                    except json.JSONDecodeError: continue
        except OSError: continue
    events.sort(key=lambda x: x.get("timestamp_ms", 0))
    return events

def analyze_route_actions():
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    # Store aggregated actions for each of the main routes
    route_stats = defaultdict(lambda: {
        "event_types": Counter(),
        "clicks": Counter(), # CSS selectors or names
        "form_inputs": Counter(),
        "apps": Counter(),
        "window_titles": Counter(),
        "shortcuts": Counter(),
        "total_duration_ms": 0,
        "visit_count": 0,
        "clipboard_changes": 0
    })
    
    # Track actions globally to dump sample sessions
    
    for session_dir in sorted(DATASET.iterdir()):
        if not session_dir.is_dir(): continue
        events = load_events(session_dir)
        
        current_route = None
        route_start_time = None
        last_time = None
        
        for event in events:
            event_type = event.get("event_type")
            ts = event.get("timestamp_ms", 0)
            
            # Identify current route from browser navigation or active browser tab context
            url = get_url(event)
            if url:
                parsed = get_route(event)
                if parsed:
                    route = parsed
                    if route.startswith("#"): route = route[1:]
                    if route != current_route:
                        # Close previous route
                        if current_route and route_start_time and last_time:
                            route_stats[current_route]["total_duration_ms"] += (last_time - route_start_time)
                            route_stats[current_route]["visit_count"] += 1
                        current_route = route
                        route_start_time = ts
            
            last_time = ts
            if not current_route: continue
            
            stats = route_stats[current_route]
            stats["event_types"][event_type] += 1
            
            ctx = event.get("context")
            if not ctx: ctx = {}
            active_app = ctx.get("active_app")
            if not isinstance(active_app, dict): active_app = {}
            
            # Active App
            app_name = active_app.get("app_name")
            if app_name: stats["apps"][app_name] += 1
            
            # Window Title
            window_title = active_app.get("window_title")
            if window_title: stats["window_titles"][window_title] += 1
            
            payload = event.get("payload")
            if not payload: payload = {}
            if event_type == "clipboard_change":
                stats["clipboard_changes"] += 1
            elif event_type == "browser_click":
                element = payload.get("element")
                if not isinstance(element, dict): element = {}
                attrs = element.get("attributes")
                if not isinstance(attrs, dict): attrs = {}
                name = attrs.get("name") or attrs.get("id") or element.get("text") or attrs.get("class")
                if name: stats["clicks"][name] += 1
            elif event_type == "browser_form_input":
                element = payload.get("element")
                if not isinstance(element, dict): element = {}
                attrs = element.get("attributes")
                if not isinstance(attrs, dict): attrs = {}
                name = attrs.get("name") or attrs.get("id") or attrs.get("placeholder")
                if name: stats["form_inputs"][name] += 1
            elif event_type == "shortcut":
                shortcut = payload.get("shortcut")
                if shortcut: stats["shortcuts"][shortcut] += 1

        if current_route and route_start_time and last_time:
            route_stats[current_route]["total_duration_ms"] += (last_time - route_start_time)
            route_stats[current_route]["visit_count"] += 1

    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for route, stats in sorted(route_stats.items(), key=lambda x: x[1]["visit_count"], reverse=True):
            if stats["visit_count"] < 5: continue # Skip rare routes
            out.write(f"=== ROUTE: {route} ===\n")
            out.write(f"Visits: {stats['visit_count']}\n")
            avg_dur = stats['total_duration_ms'] / stats['visit_count'] / 1000 if stats['visit_count'] else 0
            out.write(f"Avg Duration: {avg_dur:.2f} s\n")
            out.write(f"Clipboard Changes: {stats['clipboard_changes']}\n")
            
            out.write("Top Apps:\n")
            for k, v in stats["apps"].most_common(5): out.write(f"  {k}: {v}\n")
            
            out.write("Top Window Titles:\n")
            for k, v in stats["window_titles"].most_common(5): out.write(f"  {k}: {v}\n")
            
            out.write("Top Event Types:\n")
            for k, v in stats["event_types"].most_common(5): out.write(f"  {k}: {v}\n")
            
            out.write("Top Browser Clicks:\n")
            for k, v in stats["clicks"].most_common(10): out.write(f"  {k}: {v}\n")
            
            out.write("Top Form Inputs:\n")
            for k, v in stats["form_inputs"].most_common(10): out.write(f"  {k}: {v}\n")
            
            out.write("Top Shortcuts:\n")
            for k, v in stats["shortcuts"].most_common(5): out.write(f"  {k}: {v}\n")
            out.write("\n")

if __name__ == "__main__":
    analyze_route_actions()
