import os
import sys
import json
from scraper import get_all_raw_jobs
from ai_processor import process_jobs_with_gemini
from telegram_notifier import send_telegram_job_alert

# Siguran ispis za Windows konzolu
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_job_radar():
    print("=" * 60)
    print("POKRECEM STYRIE JOB RADAR (TRIEBEN & OBERSTEIERMARK)")
    print("=" * 60)

    # 1. Prikupljanje sirovih poslova
    raw_jobs = get_all_raw_jobs()

    # 2. AI Evaluacija i prevod na FR i DE
    print("\nObrada i prilagodba profilu (Back Office / Remote / FR-DE)...")
    data = process_jobs_with_gemini(raw_jobs)

    # 3. Snimanje u docs/data.json za Web Dashboard
    os.makedirs("docs", exist_ok=True)
    json_path = os.path.join("docs", "data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nUspjesno sacuvano {len(data.get('jobs', []))} poslova u {json_path}!")

    # 4. Slanje notifikacije na Telegram na francuskom
    print("\nSlanje jutarnjeg brifinga na Telegram grupu (Francuski jezik)...")
    send_telegram_job_alert(data)

    print("\n" + "=" * 60)
    print("ZAVRSENO USPJESNO!")
    print("=" * 60)

if __name__ == "__main__":
    run_job_radar()
