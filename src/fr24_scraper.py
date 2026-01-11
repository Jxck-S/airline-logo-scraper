import requests
from bs4 import BeautifulSoup

URL = "https://www.flightradar24.com/data/airlines/"
from .config import HEADERS

def get_fr24_map():
    """
    Scrapes FR24 airlines page and returns a dictionary: {ICAO: logo_url}
    """
    print(f"Scraping {URL} for logo map...")
    icao_map = {}
    try:
        r = requests.get(URL, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(f"Failed to fetch FR24 data: {r.status_code}")
            return icao_map

        soup = BeautifulSoup(r.text, 'html.parser')
        tables = soup.find_all('table')
        
        # We assume the main table is the one with many rows. Inspect showed Table 0.
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                # A data row typically has ~6 columns. The one we saw had class="w40..." etc.
                if len(cols) < 4:
                    continue
                
                # Column index 3 (0-based) usually has Codes: "2I / CSB" or "EMC"
                # Let's inspect Col 3
                code_text = cols[3].get_text(strip=True)
                
                # Logic to extract ICAO (3 chars). IATA is 2 chars.
                # Common formats: "IATA / ICAO", "ICAO", "- / ICAO"
                parts = [p.strip() for p in code_text.split('/')]
                
                icao = None
                for p in parts:
                    if len(p) == 3:
                        icao = p
                        break
                
                if not icao:
                    continue
                    
                # Column 1 has the image
                # <img ... data-bn-lazy-src="...">
                img_tag = cols[1].find('img')
                if img_tag and img_tag.get('data-bn-lazy-src'):
                    url = img_tag.get('data-bn-lazy-src')
                    icao_map[icao] = url
                    
    except Exception as e:
        print(f"Error scraping FR24: {e}")
        
    print(f"Found {len(icao_map)} airlines with logos from FR24 index.")
    return icao_map

if __name__ == "__main__":
    # Test run
    mapping = get_fr24_map()
    print("Sample entries:")
    keys = list(mapping.keys())[:10]
    for k in keys:
        print(f"{k}: {mapping[k]}")
