import json
from pathlib import Path
from datetime import datetime
from jsonschema import validate
from benchmark import load_gt_manifest, score_segments
from segmenter_v2 import run_segmentation

DATASET_B_PATH = Path("dataset_b")
DATASET_A_PATH = Path("dataset_a")
SEGMENTS_JSONL = Path("version_2/segments.jsonl")

# Schema for Stage 1
schema = {
    "type": "object",
    "properties": {
        "session_id": {"type": "string"},
        "start": {"type": "string", "format": "date-time"},
        "end": {"type": "string", "format": "date-time"},
        "label": {"type": "string"}
    },
    "required": ["session_id", "start", "end", "label"]
}

def stage_1():
    print("=== Stage 1: Schema & Logical Integrity ===")
    session_ids = set([d.name for d in DATASET_B_PATH.iterdir() if d.is_dir()])
    last_end = {}
    
    with open(SEGMENTS_JSONL, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            data = json.loads(line)
            validate(instance=data, schema=schema)
            
            # Iso format & temporal logic
            start = datetime.fromisoformat(data['start'].replace("Z", "+00:00"))
            end = datetime.fromisoformat(data['end'].replace("Z", "+00:00"))
            assert start < end, f"Line {i}: start >= end"
            
            # No session overlap
            sess = data['session_id']
            if sess in last_end:
                assert start >= last_end[sess], f"Line {i}: overlapping segment in {sess}"
            last_end[sess] = end
            
            # Session exists
            assert sess in session_ids, f"Line {i}: invalid session {sess}"
            
    print("Stage 1 passed.\n")

def stage_2():
    print("=== Stage 2: Quantitative Benchmark ===")
    gt = load_gt_manifest(DATASET_A_PATH)
    preds = run_segmentation(DATASET_A_PATH, idle_threshold=60.0, brief_switch=5.0) # Best params
    scores = score_segments(preds, gt)
    
    print(f"Avg IoU: {scores['Avg_IoU']:.3f} (Target: >= 0.65)")
    print(f"F1 Score: {scores['F1_Boundary']:.3f} (Target: >= 0.75)")
    print(f"Segmentation Ratio: {scores['Segmentation_Ratio']:.3f} (Target: ~1.0)")
    print(f"ARI: {scores['ARI']:.3f} (Target: >= 0.70)")
    print("Stage 2 completed.\n")

def stage_3():
    print("=== Stage 3: Statistical Sanity Checks ===")
    with open(SEGMENTS_JSONL, 'r', encoding='utf-8') as f:
        segments = [json.loads(line) for line in f]
    
    labels = set([s['label'] for s in segments])
    print(f"Distinct Labels: {len(labels)} (Target: 3-8)")
    
    durations = [(datetime.fromisoformat(s['end'].replace("Z", "+00:00")) - datetime.fromisoformat(s['start'].replace("Z", "+00:00"))).total_seconds() for s in segments]
    avg_dur = sum(durations)/len(durations) if durations else 0
    print(f"Avg Duration: {avg_dur:.1f}s (Target: 45s - 900s)")
    
    # Active Coverage Ratio
    # Simple estimate: active duration / total session time
    # This requires dataset B total time, we can approximate it.
    print(f"Total Segments: {len(segments)}")
    
    label_counts = {l: 0 for l in labels}
    for s in segments: label_counts[s['label']] += 1
    total = len(segments)
    print("Label Frequency Distribution:")
    for l, c in label_counts.items():
        safe_l = l.encode('unicode_escape').decode() if l else 'None'
        print(f"  {safe_l}: {c/total*100:.1f}%")
        
    print("Stage 3 completed.\n")

if __name__ == "__main__":
    stage_1()
    stage_2()
    stage_3()
