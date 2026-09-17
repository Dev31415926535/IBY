import json
from pathlib import Path
from collections import Counter, defaultdict

DATASET = Path("dataset_a")

domains = Counter()
urls_by_domain = defaultdict(Counter)

for session_dir in sorted(DATASET.iterdir()):
    if not session_dir.is_dir():
        continue

    for events_file in session_dir.rglob("events.jsonl"):
        with events_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event.get("event_type") != "browser_navigation":
                    continue

                payload = event.get("payload") or {}

                url = (
                    payload.get("url")
                    or payload.get("target_url")
                    or payload.get("href")
                    or ""
                )

                if url:
                    from urllib.parse import urlparse

                    parsed = urlparse(url)
                    domain = parsed.netloc or parsed.path
                    domains[domain] += 1
                    urls_by_domain[domain][url] += 1

print("Navigation domains:")
for domain, count in domains.most_common():
    print(f"\n{domain}: {count}")
    for url, url_count in urls_by_domain[domain].most_common(10):
        print(f"  {url_count:4} {url}")