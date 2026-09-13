import json
import re
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

DATASET_B = Path("dataset_b")
OUTPUT_FILE = Path("segments.jsonl")

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

def get_process_label(event, current_label):
    route = get_route(event)
    if route:
        if route.startswith("#"): route = route[1:]
        if route == "/payroll-items": return "payroll_items"
        if route == "/leave-applications": return "leave_applications"
        if route == "/social-insurance": return "social_insurance"
        if route == "/onboarding": return "onboarding"
        if route == "/resident-tax": return "resident_tax"
    
    ctx = event.get("context")
    if not ctx: ctx = {}
    active_app = ctx.get("active_app")
    if not isinstance(active_app, dict): active_app = {}
    
    window_title = active_app.get("window_title", "")
    if "keiyaku_kaijo" in window_title.lower(): return "contract_cancellation"
    if "settai_keihi" in window_title.lower(): return "entertainment_expense"
    if "gyomu_itaku" in window_title.lower(): return "outsourcing_expense"
    if "budget_analysis" in window_title.lower(): return "budget_analysis"
    if "nyusha_checklist" in window_title.lower(): return "onboarding_checklist"
    if "shinkuitorihikisaki" in window_title.lower(): return "new_vendor_registration"
    
    return current_label

def segment_dataset():
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for session_dir in sorted(DATASET_B.iterdir()):
            if not session_dir.is_dir(): continue
            events = load_events(session_dir)
            
            current_label = None
            segment_start = None
            last_ts = None
            
            for event in events:
                ts = event.get("timestamp_iso")
                if not ts: continue
                
                label = get_process_label(event, current_label)
                
                if label != current_label:
                    if current_label and segment_start and last_ts:
                        # Output previous segment if it lasted at least 5 seconds
                        start_time = datetime.fromisoformat(segment_start.replace("Z", "+00:00"))
                        end_time = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                        if (end_time - start_time).total_seconds() > 5:
                            out.write(json.dumps({
                                "session_id": session_dir.name,
                                "start": segment_start,
                                "end": last_ts,
                                "label": current_label
                            }) + "\n")
                    
                    current_label = label
                    segment_start = ts
                
                last_ts = ts
                
            if current_label and segment_start and last_ts:
                start_time = datetime.fromisoformat(segment_start.replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                if (end_time - start_time).total_seconds() > 5:
                    out.write(json.dumps({
                        "session_id": session_dir.name,
                        "start": segment_start,
                        "end": last_ts,
                        "label": current_label
                    }) + "\n")

if __name__ == "__main__":
    segment_dataset()
