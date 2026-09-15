import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Dict

def get_url(event):
    payload = event.get("payload") or {}
    for key in ["url", "target_url", "href"]:
        val = payload.get(key)
        if val: return val
    ctx = event.get("context") or {}
    context_url = ctx.get("active_browser_tab", {}).get("url") if isinstance(ctx.get("active_browser_tab"), dict) else None
    return context_url

def get_route(event):
    url = get_url(event)
    if not url: return None
    try:
        parsed = urlparse(url)
        return parsed.fragment if parsed.fragment else parsed.path
    except Exception:
        return None

def load_events(session_dir: Path) -> List[Dict]:
    events = []
    for f in sorted(session_dir.rglob("events.jsonl")):
        try:
            with f.open("r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line: continue
                    try:
                        e = json.loads(line)
                        if isinstance(e, dict): events.append(e)
                    except json.JSONDecodeError: continue
        except OSError: continue
    events.sort(key=lambda x: x.get("timestamp_ms", 0))
    return events

def get_label(event):
    route = get_route(event)
    if route:
        if route.startswith("#"): route = route[1:]
        if route == "/payroll-items": return "給与備考・控除整備"
        if route == "/leave-applications": return "育児・産休申請確認"
        if route == "/social-insurance": return "社保・年金補正対応"
        if route == "/onboarding": return "入社照合・手当確認"
        if route == "/resident-tax": return "住民税通知確認"
    
    ctx = event.get("context") or {}
    app = ctx.get("active_app") or {}
    window = app.get("window_title", "")
    
    if "keiyaku_kaijo" in window.lower(): return "契約解除手続き"
    if "settai_keihi" in window.lower(): return "接待経費規定"
    if "gyomu_itaku" in window.lower(): return "業務委託経費規定"
    if "budget_analysis" in window.lower(): return "予算差異分析"
    if "nyusha_checklist" in window.lower(): return "入社チェックリスト新卒バッチ"
    if "shinkuitorihikisaki" in window.lower(): return "新規取引先登録手続き"
    
    return None

def segment_session(events: List[Dict], idle_threshold: float, brief_app_switch_threshold: float) -> List[Dict]:
    segments = []
    current_label = None
    segment_start = None
    last_ts = None
    
    for event in events:
        ts_str = event.get("timestamp_iso")
        if not ts_str: continue
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        
        # Check idle gap
        if last_ts and (ts - last_ts).total_seconds() > idle_threshold:
            if current_label and segment_start:
                duration = (last_ts - segment_start).total_seconds()
                if duration >= 5.0:
                    segments.append({
                        "start": segment_start,
                        "end": last_ts,
                        "label": current_label
                    })
                current_label = None
                segment_start = None
        
        label = get_label(event)
        
        if label:
            if current_label is None:
                current_label = label
                segment_start = ts
            elif current_label != label:
                # Label changed. Is it a brief switch or permanent change?
                # Actually, our simple segmenter will just split. 
                # Let's say if we are in a segment, and we hit a DIFFERENT labeled event,
                # we close the previous.
                if segment_start and last_ts:
                    duration = (last_ts - segment_start).total_seconds()
                    if duration >= 5.0:
                        segments.append({
                            "start": segment_start,
                            "end": last_ts,
                            "label": current_label
                        })
                current_label = label
                segment_start = ts
        else:
            # We hit an event with no label (e.g. idle desktop, notepad)
            # Should we end the current segment?
            # We'll allow brief departures (app switches) if they return within brief_app_switch_threshold
            pass # Keep current_label active until idle_threshold or new label is found
            
        last_ts = ts
        
    if current_label and segment_start and last_ts:
        duration = (last_ts - segment_start).total_seconds()
        if duration >= 5.0:
            segments.append({
                "start": segment_start,
                "end": last_ts,
                "label": current_label
            })
            
    return segments

def run_segmentation(dataset_path: Path, idle_threshold: float = 30.0, brief_switch: float = 15.0) -> Dict[str, List[Dict]]:
    predictions = {}
    for session_dir in sorted(dataset_path.iterdir()):
        if not session_dir.is_dir(): continue
        events = load_events(session_dir)
        segs = segment_session(events, idle_threshold, brief_switch)
        predictions[session_dir.name] = segs
    return predictions

if __name__ == "__main__":
    pass
