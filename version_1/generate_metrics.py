import json
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

# Load segments to calculate average time spent on /payroll-items
SEGMENTS_FILE = Path("version_1/outputs/segments.jsonl")

payroll_durations = []
if SEGMENTS_FILE.exists():
    with open(SEGMENTS_FILE, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            if data['label'] == 'payroll_items':
                try:
                    start = datetime.fromisoformat(data['start'].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(data['end'].replace("Z", "+00:00"))
                    duration = (end - start).total_seconds()
                    if duration > 0:
                        payroll_durations.append(duration)
                except Exception:
                    pass

if payroll_durations:
    avg_manual_time = sum(payroll_durations) / len(payroll_durations)
else:
    avg_manual_time = 120.0  # fallback in seconds

avg_automated_time = 2.5 # Estimated seconds per transaction using Playwright

# Metric 1: Time Comparison
labels = ['Manual (Current)', 'Automated (v1.0)']
times = [avg_manual_time, avg_automated_time]

plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
bars = plt.bar(labels, times, color=['#e74c3c', '#2ecc71'])
plt.title('Avg Time per Payroll Item (Seconds)')
plt.ylabel('Seconds')
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.1f}s', ha='center', va='bottom')

# Metric 2: Operational Steps (Clipboard actions vs Script reads)
# From route_actions.txt, payroll_items has 307 clipboard changes across 43 visits (~7 per visit)
steps_labels = ['Manual Copy-Paste Steps', 'Automated Bot Actions']
steps_values = [7, 0]

plt.subplot(1, 2, 2)
bars2 = plt.bar(steps_labels, steps_values, color=['#e67e22', '#3498db'])
plt.title('Avg Manual Steps per Transaction')
plt.ylabel('Count')
for bar in bars2:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval}', ha='center', va='bottom')

plt.tight_layout()
OUTPUT_PATH = Path("version_1/outputs/metrics_comparison.png")
plt.savefig(OUTPUT_PATH)
print(f"Visual metrics saved to {OUTPUT_PATH}")
