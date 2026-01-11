import requests
from bs4 import BeautifulSoup

from .config import HEADERS
def get_faa_codes():

    url = "https://www.faa.gov/air_traffic/publications/atpubs/cnt_html/chap3_section_3.html"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(f"Failed to fetch FAA codes: {response.status_code}")
            return set()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # The FAA page usually has tables with class "col-collapse-table" or just generic tables
        # Based on content inspection, we look for rows with 3Ltr code.
        rows = soup.find_all('tr')
        faa_icaos = set()
        
        for row in rows:
            cols = row.find_all('td')
            # Expecting columns: 3Ltr, Company, Country, Telephony
            if len(cols) >= 4:
                icao = cols[0].get_text(strip=True)
                if len(icao) == 3 and icao.isalnum():
                    faa_icaos.add(icao)
                    
        return faa_icaos
    except Exception as e:
        print(f"Error scraping FAA: {e}")
        return set()

def get_airline_codes():
    


    # Source 1: Wikipedia
    url = "https://en.wikipedia.org/wiki/List_of_airline_codes"
    
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable'})
    
    wiki_codes = []
    wiki_icao_set = set() # Set for uniqueness within Wiki
    
    if table:
        for row in table.findAll('tr'):
            columns = row.findAll('td')
            if columns:
                iata_code = columns[0].get_text().strip()
                icao_code = columns[1].get_text().strip()
                if icao_code and len(icao_code) == 3 and icao_code not in wiki_icao_set:
                    wiki_icao_set.add(icao_code)
                    wiki_codes.append((iata_code, icao_code))

    # Source 2: FAA
    faa_icao_set = get_faa_codes()

    # Stats Calculation
    intersection = wiki_icao_set.intersection(faa_icao_set)
    unique_wiki = wiki_icao_set - faa_icao_set
    unique_faa = faa_icao_set - wiki_icao_set
    
    # Combined List
    combined_codes = list(wiki_codes) # Start with Wiki (has IATA)
    for icao in unique_faa:
        combined_codes.append((None, icao)) # Add FAA-only (No IATA known here)
    
    total_combined = len(combined_codes)

    # Print Stats
    print("\n" + "="*60)
    print(f"{'Source Stats':^60}")
    print("="*60)
    print(f"{'Wikipedia':<20} | {len(wiki_icao_set):>10} codes")
    print(f"{'FAA (Chap 3)':<20} | {len(faa_icao_set):>10} codes")
    print("-" * 60)
    print(f"{'Intersection':<20} | {len(intersection):>10}")
    print(f"{'Unique to Wiki':<20} | {len(unique_wiki):>10}")
    print(f"{'Unique to FAA':<20} | {len(unique_faa):>10}")
    print("-" * 60)
    print(f"{'TOTAL COMBINED':<20} | {total_combined:>10} airlines")
    print("="*60 + "\n")

    return combined_codes
