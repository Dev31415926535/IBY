import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATASET = Path("dataset_a")
OUTPUT_FILE = Path("version_1/outputs/ground_truth_analysis.txt")

def parse_time(ts_str):
    if not ts_str: return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None

def analyze_gt():
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    process_families = defaultdict(int)
    process_variants = defaultdict(int)
    suspensions = 0
    resumptions = 0
    switch_outs = 0
    
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for session_dir in sorted(DATASET.iterdir()):
            if not session_dir.is_dir(): continue
            
            gt_file = session_dir / "gt.jsonl"
            manifest_file = session_dir / "gt_manifest.json"
            
            if not gt_file.exists() or not manifest_file.exists():
                continue
                
            out.write(f"=== Session: {session_dir.name} ===\n")
            
            with manifest_file.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
                processes = manifest.get("processes", [])
                for p in processes:
                    family = p.get("family_name")
                    process_families[family] += 1
                    executions = p.get("executions", [])
                    out.write(f"  Process: {family}\n")
                    for ex in executions:
                        variant = ex.get("variant")
                        process_variants[variant] += 1
                        case_id = ex.get("case_id")
                        apps = ex.get("apps", [])
                        out.write(f"    Exec: {case_id} | Variant: {variant} | Apps: {apps}\n")
                        out.write(f"    Start: {ex.get('start_ts')} | End: {ex.get('end_ts')}\n")
                        if ex.get("continues_from_prev"): out.write("      Continues from prev chunk\n")
                        if ex.get("continues_to_next"): out.write("      Continues to next chunk\n")
            
            with gt_file.open("r", encoding="utf-8") as f:
                out.write("  Events:\n")
                for line in f:
                    if not line.strip(): continue
                    event = json.loads(line)
                    etype = event.get("event")
                    ts = event.get("ts_utc")
                    if etype == "process_started":
                        out.write(f"    {ts} - STARTED: {event.get('process_name')} (Case: {event.get('case_id')})\n")
                    elif etype == "process_switched_out":
                        out.write(f"    {ts} - SWITCH_OUT: from {event.get('from')} to {event.get('to')}\n")
                        switch_outs += 1
                    elif etype == "process_suspended":
                        out.write(f"    {ts} - SUSPENDED: {event.get('from')}\n")
                        suspensions += 1
                    elif etype == "process_resumed":
                        out.write(f"    {ts} - RESUMED: {event.get('process_code')} (Phase {event.get('phase')})\n")
                        resumptions += 1
                    elif etype == "task_started":
                        out.write(f"    {ts} - TASK: {event.get('action')} on {event.get('entity')}\n")
            out.write("\n")
            
        out.write("=== SUMMARY ===\n")
        out.write("Process Families:\n")
        for k, v in process_families.items(): out.write(f"  {k}: {v}\n")
        out.write("Process Variants:\n")
        for k, v in process_variants.items(): out.write(f"  {k}: {v}\n")
        out.write(f"Total Suspensions: {suspensions}\n")
        out.write(f"Total Resumptions: {resumptions}\n")
        out.write(f"Total Switch-outs: {switch_outs}\n")

if __name__ == "__main__":
    analyze_gt()
