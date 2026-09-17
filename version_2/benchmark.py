import json
from pathlib import Path
from datetime import datetime
from sklearn.metrics import adjusted_rand_score
from typing import List, Dict, Tuple

def load_gt_manifest(dataset_path: Path) -> Dict[str, List[Dict]]:
    gt_intervals = {}
    for session_dir in sorted(dataset_path.iterdir()):
        if not session_dir.is_dir(): continue
        manifest_path = session_dir / "gt_manifest.json"
        if not manifest_path.exists(): continue
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        session_id = session_dir.name
        if session_id not in gt_intervals:
            gt_intervals[session_id] = []
            
        for process in data.get("processes", []):
            code = process.get("code")
            for exec_data in process.get("executions", []):
                start_ts = exec_data.get("start_ts")
                end_ts = exec_data.get("end_ts")
                if start_ts and end_ts:
                    gt_intervals[session_id].append({
                        "start": datetime.fromisoformat(start_ts.replace("Z", "+00:00")),
                        "end": datetime.fromisoformat(end_ts.replace("Z", "+00:00")),
                        "label": code
                    })
    return gt_intervals

def compute_iou(p_start: datetime, p_end: datetime, g_start: datetime, g_end: datetime) -> float:
    intersection_start = max(p_start, g_start)
    intersection_end = min(p_end, g_end)
    intersection_duration = max(0.0, (intersection_end - intersection_start).total_seconds())
    
    union_duration = (p_end - p_start).total_seconds() + (g_end - g_start).total_seconds() - intersection_duration
    
    if union_duration == 0:
        return 0.0
    return intersection_duration / union_duration

def score_segments(predictions: Dict[str, List[Dict]], ground_truths: Dict[str, List[Dict]], tol_seconds=15.0):
    total_gt = 0
    total_pred = 0
    total_iou_matches = 0
    sum_iou = 0.0
    total_comparisons = 0
    
    true_positives = 0
    
    pred_labels_aligned = []
    gt_labels_aligned = []

    for session_id, gt_list in ground_truths.items():
        pred_list = predictions.get(session_id, [])
        total_gt += len(gt_list)
        total_pred += len(pred_list)
        
        # Greedy matching for IoU
        matched_gt = set()
        for p in pred_list:
            best_iou = 0
            best_g_idx = -1
            for g_idx, g in enumerate(gt_list):
                if g_idx in matched_gt: continue
                iou = compute_iou(p['start'], p['end'], g['start'], g['end'])
                if iou > best_iou:
                    best_iou = iou
                    best_g_idx = g_idx
            
            if best_g_idx != -1 and best_iou >= 0.5:
                matched_gt.add(best_g_idx)
                total_iou_matches += 1
                pred_labels_aligned.append(p['label'])
                gt_labels_aligned.append(gt_list[best_g_idx]['label'])
            
            # Check boundaries for Precision/Recall
            # We count a predicted boundary as TP if there is ANY gt boundary within tolerance
            start_matched = any(abs((p['start'] - g['start']).total_seconds()) <= tol_seconds for g in gt_list)
            end_matched = any(abs((p['end'] - g['end']).total_seconds()) <= tol_seconds for g in gt_list)
            if start_matched and end_matched:
                true_positives += 1

            if best_iou > 0:
                sum_iou += best_iou
                total_comparisons += 1

    avg_iou = sum_iou / total_comparisons if total_comparisons > 0 else 0
    precision = true_positives / total_pred if total_pred > 0 else 0
    recall = true_positives / total_gt if total_gt > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    ari = adjusted_rand_score(gt_labels_aligned, pred_labels_aligned) if len(gt_labels_aligned) > 1 else 0
    segmentation_ratio = total_pred / total_gt if total_gt > 0 else 0
    
    return {
        "Avg_IoU": avg_iou,
        "F1_Boundary": f1,
        "Segmentation_Ratio": segmentation_ratio,
        "ARI": ari,
        "Matches_IoU_0.5": total_iou_matches,
        "Total_GT": total_gt,
        "Total_Pred": total_pred
    }

if __name__ == "__main__":
    pass
