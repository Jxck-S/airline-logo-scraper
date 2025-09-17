import requests
from bs4 import BeautifulSoup


def get_airline_codes():
    
    headers = {
        'User-Agent' : "AirlineLogoScraper/1.0"
    } # set user agent for get access to wikipedia data

    url = "https://en.wikipedia.org/wiki/List_of_airline_codes"
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable'})
    codes = []
    unique_icao_codes = set()  # Set to keep track of unique ICAO codes

    for row in table.findAll('tr'):
        columns = row.findAll('td')
        if columns:
            iata_code = columns[0].get_text().strip()
            icao_code = columns[1].get_text().strip()
            if icao_code and icao_code not in unique_icao_codes:  # Check for unique ICAO code
                unique_icao_codes.add(icao_code)  # Add to the set if unique
                codes.append((iata_code, icao_code))

    return codes
