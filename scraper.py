import sys
import urllib.request
import urllib.parse
import re
import json
import xml.etree.ElementTree as ET

# Siguran ispis za Windows konzolu
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de-AT,de;q=0.9,en;q=0.8'
}

def fetch_karriere_jobs():
    """Dohvata poslove sa karriere.at za Trieben, Rottenmann, Liezen, Leoben, Schladming i okolinu"""
    urls = [
        ("Trieben", "https://www.karriere.at/jobs/trieben"),
        ("Rottenmann (~10km)", "https://www.karriere.at/jobs/rottenmann"),
        ("Liezen Administration", "https://www.karriere.at/jobs/administration/liezen-bezirk"),
        ("Liezen Büro", "https://www.karriere.at/jobs/buero/liezen-bezirk"),
        ("Liezen Sales Assistenz", "https://www.karriere.at/jobs/sales-assistenz/liezen-bezirk"),
        ("Admont (~25km)", "https://www.karriere.at/jobs/admont"),
        ("Kalwang (~18km)", "https://www.karriere.at/jobs/kalwang"),
        ("Leoben Bezirk Administration", "https://www.karriere.at/jobs/administration/leoben-bezirk"),
        ("Schladming", "https://www.karriere.at/jobs/schladming")
    ]
    
    collected = []
    seen_urls = set()
    
    for category_label, url in urls:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # Regex za hvatanje job kartica
                raw_matches = re.findall(r'href="(/jobs/\d+|https://www\.karriere\.at/jobs/\d+)"[^>]*>([^<]+)</a>', html)
                
                for raw_link, title in raw_matches:
                    clean_title = title.strip().replace('&amp;', '&').replace('&quot;', '"')
                    if len(clean_title) < 4 or "karriere" in clean_title.lower():
                        continue
                    
                    full_link = raw_link if raw_link.startswith('http') else f"https://www.karriere.at{raw_link}"
                    if full_link in seen_urls:
                        continue
                    seen_urls.add(full_link)
                    
                    collected.append({
                        "source": "karriere.at",
                        "category_label": category_label,
                        "title": clean_title,
                        "url": full_link
                    })
        except Exception as e:
            # Preskoci tiho ako grad nema trenutno direktnu stranicu
            pass
            
    return collected

def fetch_google_job_rss():
    """Dohvata najnovije poslove sa Google RSS (Willhaben, AMS, Steirerjobs, Leihfirme, itd.)"""
    queries = [
        # 1. Willhaben & Steirerjobs Liezen / Trieben / Rottenmann
        'site:willhaben.at/jobs ("Liezen" OR "Trieben" OR "Rottenmann" OR "Kalwang" OR "Admont")',
        'site:steirerjobs.at ("Liezen" OR "Trieben" OR "Rottenmann" OR "Leoben")',
        
        # 2. AMS Österreich (eJob-Room)
        'site:ams.at ("Liezen" OR "Trieben" OR "Rottenmann") (Büro OR Administration OR Assistent OR Sachbearbeiter)',
        
        # 3. Leihfirme u Štajerskoj (Trenkwalder, Adecco, Powerserv, Hofmann, TTI, Manpower, Transfer)
        '("Liezen" OR "Trieben" OR "Rottenmann" OR "Leoben") ("Trenkwalder" OR "Adecco" OR "Powerserv" OR "Hofmann Personal" OR "TTI" OR "Manpower" OR "Transfer Personal") (Büro OR Administration OR Assistent OR Sachbearbeiter OR Empfang OR Kundenservice)',
        
        # 4. Opšti regionalni oglasi za uredske poslove
        '("Liezen" OR "Trieben" OR "Rottenmann" OR "Selzthal" OR "Admont") ("Büro" OR "Administration" OR "Assistent" OR "Sachbearbeiter" OR "Backoffice" OR "Vertriebsinnendienst") job',
        
        # 5. Remote / Home Office poslovi širom Austrije (posebno višejezični)
        'Österreich ("Home Office" OR "Remote" OR "Télétravail") ("Customer Support" OR "Kundenservice" OR "Backoffice" OR "Sachbearbeiter" OR "Administration" OR "Französisch" OR "French" OR "Sales Assistant") job',
        
        # 6. MetaJob & StepStone za Obersteiermark
        'site:metajob.at ("Liezen" OR "Trieben" OR "Rottenmann") (Büro OR Administration OR Assistent)'
    ]
    
    collected = []
    seen_urls = set()
    
    for q in queries:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=de&gl=AT&ceid=AT:de"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as response:
                root = ET.fromstring(response.read())
                for item in root.findall(".//item")[:15]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    
                    if not title or link in seen_urls:
                        continue
                    seen_urls.add(link)
                    
                    collected.append({
                        "source": "Google/Willhaben/AMS/Leihfirmen",
                        "category_label": "Regional/RSS",
                        "title": title.strip(),
                        "url": link,
                        "published": pub_date
                    })
        except Exception as e:
            pass
            
    return collected

def get_all_raw_jobs():
    print("Prikupljam poslove sa karriere.at (Trieben, Rottenmann, Liezen, Leoben, Schladming)...")
    karriere_jobs = fetch_karriere_jobs()
    print(f"Pronadjeno na karriere.at: {len(karriere_jobs)}")
    
    print("Prikupljam poslove sa Willhaben, AMS, Steirerjobs, Leihfirmen i Remote...")
    rss_jobs = fetch_google_job_rss()
    print(f"Pronadjeno na agregatorima i Leihfirmama: {len(rss_jobs)}")
    
    all_jobs = karriere_jobs + rss_jobs
    print(f"Ukupno prikupljeno sirovih oglasa: {len(all_jobs)}")
    return all_jobs

if __name__ == "__main__":
    jobs = get_all_raw_jobs()
    print(f"Uspjesno ucitano {len(jobs)} poslova.")
    for j in jobs[:5]:
        print(f"- [{j['source']}] {j['title']} -> {j['url']}")
