import os
import sys
import json
import urllib.request
from datetime import datetime

# Siguran ispis za Windows konzolu
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://faruk-salkic.github.io/steiermark-job-finder/")

def send_telegram_job_alert(data):
    """Šalje jutarnji sažetak novih poslova na francuskom jeziku u Telegram grupu"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Upozorenje: TELEGRAM_BOT_TOKEN ili TELEGRAM_CHAT_ID nisu postavljeni. Preskacem slanje na Telegram.")
        return False

    jobs = data.get("jobs", [])
    today_fr = datetime.now().strftime("%d.%m.%Y")

    # Formiranje francuske poruke
    msg = f"☀️ <b>BONJOUR ! NOUVELLES OFFRES D'EMPLOI DU JOUR</b>\n"
    msg += f"📍 <b>Région de Trieben & Télétravail | {today_fr}</b>\n\n"
    msg += f"Voici une sélection de postes de bureau et d'assistance correspondant à ton profil multilingue :\n\n"

    for i, job in enumerate(jobs[:5], 1):
        fr = job.get("french", {})
        title = fr.get("title", "Offre d'emploi")
        loc_badge = job.get("location_badge_fr", "Styrie")
        company = job.get("company", "Entreprise")
        
        msg += f"🏢 <b>{i}. {title}</b>\n"
        msg += f"   📍 <i>{loc_badge}</i> | 🏛️ {company}\n"
        if fr.get("fit_reason"):
            msg += f"   💡 {fr['fit_reason'][:120]}...\n"
        msg += f"\n"

    msg += f"👉 <b>Consulte toutes les offres complètes et bascule en allemand en 1 clic :</b>\n"
    msg += f"{DASHBOARD_URL}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🚀 Ouvrir le Dashboard (FR / DE)", "url": DASHBOARD_URL}
            ]]
        }
    }

    try:
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as resp:
            print("Telegram poruka je uspjesno poslata!")
            return True
    except Exception as e:
        print(f"Greska pri slanju na Telegram: {e}")
        return False

if __name__ == "__main__":
    # Testiranje formata poruke
    sample_data = {
        "jobs": [
            {
                "company": "Industrie Trieben",
                "location_badge_fr": "Trieben (Sur place - 0 km)",
                "french": {
                    "title": "Assistante Back Office & Planification",
                    "fit_reason": "Directement à Trieben. Tâches administratives idéales pour niveau allemand A2/B1."
                }
            }
        ]
    }
    print("Test modul telegram_notifier.py ucitan.")
