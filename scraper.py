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
    """Dohvata poslove sa karriere.at za Trieben, Rottenmann, Liezen i Remote"""
    urls = [
        ("Trieben", "https://www.karriere.at/jobs/trieben"),
        ("Rottenmann", "https://www.karriere.at/jobs/rottenmann"),
        ("Liezen Administration", "https://www.karriere.at/jobs/administration/liezen-bezirk"),
        ("Liezen Büro", "https://www.karriere.at/jobs/buero/liezen-bezirk"),
        ("Liezen Sales Assistenz", "https://www.karriere.at/jobs/sales-assistenz/liezen-bezirk"),
        ("Remote Österreich", "https://www.karriere.at/jobs?homeOffice=1&what=Administration")
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
            print(f"Info: Preskacem {url} ({e})")
            
    return collected

def fetch_google_job_rss():
    """Dohvata najnovije poslove sa Google RSS (Willhaben, AMS, Leihfirme, itd.)"""
    queries = [
        'site:willhaben.at/jobs ("Liezen" OR "Trieben" OR "Rottenmann")',
        '("Liezen" OR "Trieben" OR "Rottenmann") ("Büro" OR "Administration" OR "Assistent" OR "Sachbearbeiter" OR "Backoffice") job',
        'Österreich ("Home Office" OR "Remote") ("Customer Service" OR "Backoffice" OR "Sachbearbeiter" OR "Administration" OR "Französisch") job'
    ]
    
    collected = []
    seen_urls = set()
    
    for q in queries:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=de&gl=AT&ceid=AT:de"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as response:
                root = ET.fromstring(response.read())
                for item in root.findall(".//item")[:10]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    
                    if not title or link in seen_urls:
                        continue
                    seen_urls.add(link)
                    
                    collected.append({
                        "source": "Google/Willhaben/Web",
                        "category_label": "Regional/RSS",
                        "title": title.strip(),
                        "url": link,
                        "published": pub_date
                    })
        except Exception as e:
            print(f"Info: Preskacem RSS za {q} ({e})")
            
    return collected

def get_all_raw_jobs():
    print("Prikupljam poslove sa karriere.at...")
    karriere_jobs = fetch_karriere_jobs()
    print(f"Pronadjeno na karriere.at: {len(karriere_jobs)}")
    
    print("Prikupljam poslove sa Google/Willhaben RSS...")
    rss_jobs = fetch_google_job_rss()
    print(f"Pronadjeno na RSS: {len(rss_jobs)}")
    
    all_jobs = karriere_jobs + rss_jobs
    print(f"Ukupno prikupljeno sirovih oglasa: {len(all_jobs)}")
    return all_jobs

if __name__ == "__main__":
    jobs = get_all_raw_jobs()
    print(f"Uspjesno ucitano {len(jobs)} poslova.")
    for j in jobs[:5]:
        print(f"- [{j['source']}] {j['title']} -> {j['url']}")
