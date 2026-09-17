import json
from pathlib import Path
from benchmark import load_gt_manifest, score_segments
from segmenter_v2 import run_segmentation

DATASET_A = Path("dataset_a")
DATASET_B = Path("dataset_b")
OUTPUT_JSONL = Path("version_2/segments.jsonl")

def tune():
    gt = load_gt_manifest(DATASET_A)
    if not gt:
        print("Ground truth not found. Please run from correct directory.")
        return
        
    idle_thresholds = [15.0, 30.0, 60.0]
    brief_switches = [5.0, 15.0, 30.0]
    
    best_f1 = -1
    best_params = (30.0, 15.0)
    
    print("Running Hyperparameter Tuning on Dataset A...")
    for it in idle_thresholds:
        for bs in brief_switches:
            preds = run_segmentation(DATASET_A, it, bs)
            scores = score_segments(preds, gt)
            print(f"Params: Idle={it}s, AppSwitch={bs}s -> F1: {scores['F1_Boundary']:.3f}, IoU: {scores['Avg_IoU']:.3f}, ARI: {scores['ARI']:.3f}")
            if scores['F1_Boundary'] > best_f1:
                best_f1 = scores['F1_Boundary']
                best_params = (it, bs)
                
    print(f"\nBest Params: Idle={best_params[0]}s, AppSwitch={best_params[1]}s with F1={best_f1:.3f}")
    
    print("\nRunning best model on Dataset B...")
    b_preds = run_segmentation(DATASET_B, best_params[0], best_params[1])
    
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for session_id, segs in b_preds.items():
            for s in segs:
                f.write(json.dumps({
                    "session_id": session_id,
                    "start": s["start"].isoformat(),
                    "end": s["end"].isoformat(),
                    "label": s["label"]
                }) + "\n")
                
    print(f"Validated segments written to {OUTPUT_JSONL}")

if __name__ == "__main__":
    tune()
