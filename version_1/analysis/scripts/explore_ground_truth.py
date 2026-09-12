import json
from pathlib import Path
from collections import Counter

dataset_path = Path("dataset_a")

event_types = Counter()
processes = Counter()
variants = Counter()
tasks = Counter()

total_records = 0
total_sessions = 0

for session_path in dataset_path.iterdir():

    if not session_path.is_dir():
        continue

    gt_path = session_path / "gt.jsonl"

    if not gt_path.exists():
        print(f"Skipping {session_path.name}: gt.jsonl not found")
        continue

    total_sessions += 1

    with gt_path.open("r", encoding="utf-8") as f:

        for line_number, line in enumerate(f, start=1):

            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(
                    f"Invalid JSON in {gt_path}, "
                    f"line {line_number}"
                )
                continue

            total_records += 1

            event_type = (
                record.get("event_type")
                or record.get("type")
                or record.get("name")
            )

            event_types[event_type] += 1

            process = record.get("current_process")
            if process is not None:
                processes[process] += 1

            variant = record.get("process_variant")
            if variant is not None:
                variants[variant] += 1

            for key in [
                "task",
                "task_name",
                "task_type",
                "activity",
                "activity_name",
            ]:
                value = record.get(key)

                if value is not None:
                    tasks[value] += 1


print("Total sessions:", total_sessions)
print("Total ground-truth records:", total_records)

print("\nEvent types:")
for key, value in event_types.most_common():
    print(f"{value:5} {key}")

print("\nProcesses:")
for key, value in processes.most_common():
    print(f"{value:5} {key}")

print("\nVariants:")
for key, value in variants.most_common():
    print(f"{value:5} {key}")

print("\nTasks:")
for key, value in tasks.most_common():
    print(f"{value:5} {key}")