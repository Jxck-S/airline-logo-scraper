import os
import requests
from PIL import Image
from io import BytesIO
import threading
import time
import concurrent.futures
from .airline_opp_codes import get_airline_codes
from .fr24_scraper import get_fr24_map
from PIL import ImageChops
from .config import HEADERS
import argparse

FA_LOGOS = "FlightAware Logos"
RB_BANNERS = "RadarBox Banners"
RB_LOGOS = "RadarBox Logos"
FR24_LOGOS = "FlightRadar24 Logos"
AVCODES_UK_BANNERS = "Avcodes UK Banners"
sources = [
    {"name": FA_LOGOS, "dir": "flightaware_logos", },
    {"name": RB_BANNERS, "dir": "radarbox_banners"},
    {"name": RB_LOGOS, "dir": "radarbox_logos"},
    {"name": FR24_LOGOS, "dir": "fr24_logos"},
    {"name": AVCODES_UK_BANNERS, "dir": "avcodes_banners"},
]

# Global Args placeholder (initialized in main)
args = None
fr24_map = {}
airline_codes = []

def main():
    global args, fr24_map
    parser = argparse.ArgumentParser(description='Airline Logo Scraper')
    parser.add_argument('-A', '--all', action='store_true', help='Download from all sources without prompting')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads (default: 10)')
    parser.add_argument('-d', '--delay', type=float, default=0.5, help='Delay between requests in seconds (default: 0.5)')
    parser.add_argument('-s', '--skip', action='store_true', help='Skip already downloaded files')
    parser.add_argument('--fr24-method', choices=['brute', 'scrape'], default='scrape', help='Method for FlightRadar24: "scrape" (default) parses their index, "brute" guesses URLs')
    args = parser.parse_args()

    # Initialize FR24 map if needed
    if args.fr24_method == 'scrape':
        pass 

    for source in sources:
        name = source['name']
        if args.all:
            source['enable'] = True
        else:
            print(f'Would you like {name}: Y/N')
            source['enable'] = input().strip().upper() == 'Y'
        if source['enable']:
            source_folder = os.path.join(".", source['dir']) # Keep using relative to cwd (root)
            os.makedirs(source_folder, exist_ok=True)

    # Load FR24 map if enabled and using scrape method
    fr24_enabled = any(s['name'] == FR24_LOGOS and s['enable'] for s in sources)
    if fr24_enabled and args.fr24_method == 'scrape':
        fr24_map = get_fr24_map()

    # START EXECUTION
    execute_scraper()

def execute_scraper():
    pass # Holder, will be wrapped below by moving code





def is_blank(img):
    # Compare the image with a blank image of the same size
    blank = Image.new(img.mode, img.size, img.getpixel((0, 0)))
    diff = ImageChops.difference(img, blank)
    
    # Check if any band has non-zero difference using getextrema
    # getbbox() handles RGBA poorly (ignores RGB diffs if Alpha diff is 0)
    for band in diff.split():
        if band.getextrema() != (0, 0):
            return False # The image is not blank
            
    return True  # The image is blank

def images_are_same(img1, img2):
    # Check if images have the same size and mode
    if img1.size != img2.size or img1.mode != img2.mode:
        return False  # The images are different

    # Compare two images to see if they are the same
    diff = ImageChops.difference(img1, img2)
    
    # Check if any band has non-zero difference
    for band in diff.split():
        if band.getextrema() != (0, 0):
            return False # The images are different
            
    return True  # The images are the same




def save_pic(url, logo_file_path, source, icao_code):
    try:
        response = None
        max_retries = 5
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                
                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < max_retries:
                        wait_time = 2 ** (attempt + 2) # 4s, 8s, 16s, 32s, 64s
                        time.sleep(wait_time)
                        continue
                    else:
                        print_log(f"Rate limit exceeded (429) for {icao_code} from {source} after retries")
                        return

                break # proceed if not 429 (success or other error handled below)
            except requests.RequestException:
                 if attempt < max_retries:
                    time.sleep(1)
                    continue
                 raise # Re-raise if final attempt fails
                 
        if not response:
             return

        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            if img.size != (1, 1) and not is_blank(img):  # Check for 1x1 and blank image
                if source == RB_LOGOS:
                    placeholder_img_path = os.path.join(os.path.dirname(__file__), 'RB_PLACERHOLDER.png')
                    placeholder_img = Image.open(placeholder_img_path)
                    if images_are_same(img, placeholder_img):
                        # print_log(f"Placeholder image received for {icao_code} from {source}, not saved.")
                        return
                img.save(logo_file_path)
                print_log(f"Downloaded {icao_code} from {source}")
                with counter_lock:
                    if source in source_counters:
                        source_counters[source] += 1
                    if source in total_counters:
                        total_counters[source] += 1
            else:
                pass
                # print_log(f"Placeholder or blank image received for {icao_code} from {source}, not saved.")
        else:
            # FlightRadar24 returns 403 for missing images, treat as 404
            is_fr24_403 = (response.status_code == 403 and source == FR24_LOGOS)
            if response.status_code != 404 and not is_fr24_403:
                print_log(f"{response.status_code} for {icao_code} {source}")
    except Exception as e:
        print_log(f"Error downloading {icao_code} from {source}: {e}")

class AirlineCode:
    def __init__(self, iata_code, icao_code):
        self.iata_code = iata_code
        self.icao_code = icao_code

    @property
    def flightaware_logo_download_url(self):
        return f"https://flightaware.com/images/airline_logos/90p/{self.icao_code}.png"

    @property
    def avcodes_uk_banner_download_url(self):
        return f"https://www.avcodes.co.uk/images/logos/{self.icao_code}.png"

    @property
    def fr24_banner_download_url(self):
        return f"https://cdn.flightradar24.com/assets/airlines/logotypes/{self.iata_code}_{self.icao_code}.png"

    @property
    def rb_banner_download_url(self):
        return f"https://cdn.radarbox.com/airlines/{self.icao_code}.png"

    @property
    def rb_logo_download_url(self):
        return f"https://cdn.radarbox.com/airlines/sq/{self.icao_code}.png"






import sys

# ... (existing imports)

# Shared counter for completed tasks
# Shared counter for completed tasks
completed_counter = 0
source_counters = {
    FA_LOGOS: 0,
    RB_BANNERS: 0,
    RB_LOGOS: 0,
    FR24_LOGOS: 0,
    AVCODES_UK_BANNERS: 0
}
total_counters = {
    FA_LOGOS: 0,
    RB_BANNERS: 0,
    RB_LOGOS: 0,
    FR24_LOGOS: 0,
    AVCODES_UK_BANNERS: 0
}
counter_lock = threading.Lock()  # Lock to synchronize access to the counter
print_lock = threading.Lock() # Lock for printing to stdout

import shutil

def format_name(name):
    if "FlightAware" in name: return "FA"
    if "RadarBox" in name:
        return "RB Ban" if "Banners" in name else "RB Log"
    if "FlightRadar24" in name: return "FR24"
    if "Avcodes" in name: return "Av"
    return name

def get_stats_string(counters, prefix):
    full_str = f"{prefix} " + " | ".join([f"{format_name(k)}:{v}" for k, v in counters.items()])
    cols = shutil.get_terminal_size().columns
    if len(full_str) > cols - 5:
        return full_str[:cols-5]
    return full_str

def get_progress_string(count, total):
    percent = (count / total) * 100
    return f"Progress: {count}/{total} ({percent:.2f}%)"

def print_log(msg):
    with print_lock:
        if 'airline_codes' in globals() and len(airline_codes) > 0:
            # Clear Line 3 (Progress)
            sys.stdout.write('\r\033[K') 
            # Move up and Clear Line 2 (Total Stats)
            sys.stdout.write('\033[F\033[K')
            # Move up and Clear Line 1 (Session Stats)
            sys.stdout.write('\033[F\033[K')
            
            print(msg)
            
            # Redraw footer
            total = len(airline_codes)
            count = completed_counter
            
            session_str = get_stats_string(source_counters, "NEW DURING skip")
            total_str = get_stats_string(total_counters, "TOTAL DIR+NEW")
            prog_str = get_progress_string(count, total)
            
            sys.stdout.write(session_str + '\033[K\n')
            sys.stdout.write(total_str + '\033[K\n')
            sys.stdout.write(prog_str + '\033[K')
        else:
            print(msg)
        sys.stdout.flush()

def print_progress():
    global completed_counter
    with counter_lock:
        completed_counter += 1
        count = completed_counter
    
    # Display progress
    total = len(airline_codes)
    if total > 0:
        session_str = get_stats_string(source_counters, "NEW DURING skip")
        total_str = get_stats_string(total_counters, "TOTAL DIR+NEW")
        prog_str = get_progress_string(count, total)
        
        with print_lock:
            # Move up to start of update region (Session + Total + Progress)
            sys.stdout.write('\r\033[F\033[F') 
            sys.stdout.write(session_str + '\033[K\n')
            sys.stdout.write(total_str + '\033[K\n')
            sys.stdout.write(prog_str + '\033[K')
            sys.stdout.flush()

use_wiki_airlines = True
if use_wiki_airlines:
    # Global set to keep track of processed ICAO codes
    processed_icao_codes = set()
    processing_lock = threading.Lock()

    
    def download_logo(code):
        global processed_icao_codes
        try:
            with processing_lock:
                if code.icao_code in processed_icao_codes:
                    return  # Skip if the code has already been processed
                processed_icao_codes.add(code.icao_code)
            
            # ... rest of your download_logo function ...
            if code.icao_code:
                request_made = False
                for source in sources:
                    if source['enable']:
                        logo_file_path = os.path.join(source['dir'], f"{code.icao_code}.png")
                        if args.skip and os.path.exists(logo_file_path):
                             continue
                        
                        if source['name'] == FA_LOGOS:
                            request_made = True
                            url = code.flightaware_logo_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == RB_BANNERS:
                            request_made = True
                            url = code.rb_banner_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == RB_LOGOS:
                            request_made = True
                            url = code.rb_logo_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == FR24_LOGOS:
                            if args.fr24_method == 'scrape':
                                if code.icao_code in fr24_map:
                                    request_made = True
                                    url = fr24_map[code.icao_code]
                                    save_pic(url, logo_file_path, source['name'], code.icao_code)
                            else: # legacy brute force
                                if code.iata_code:
                                    request_made = True
                                    url = code.fr24_banner_download_url
                                    save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == AVCODES_UK_BANNERS:
                            request_made = True
                            url = code.avcodes_uk_banner_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                
                if request_made:
                    time.sleep(args.delay)
        finally:
            print_progress()

def execute_scraper():
    # Initialize total counters
    for source in sources:
        dir_path = os.path.join(".", source['dir'])
        if os.path.exists(dir_path):
             count = len([name for name in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, name))])
             if source['name'] in total_counters:
                 total_counters[source['name']] = count

    # Reserve space for the 3-line footer (Session + Total + Progress)
    print("-" * 120)
    print('\n\n')

    global airline_codes
    # Your existing code for threading
    airline_codes = sorted(get_airline_codes(), key=lambda x: x[1]) # Sort by ICAO code
    
    # Use ThreadPoolExecutor for efficient threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for airline in airline_codes:
            iata = airline[0]
            icao = airline[1]
            code = AirlineCode(iata, icao)
            futures.append(executor.submit(download_logo, code))
        
        # Wait for all futures to complete (handled by context manager exit, but explicitly ok)
        concurrent.futures.wait(futures)

    for source in sources:
        if source['enable']:
            # Count the number of files
            dir = source['dir'] # Relative to root because we execute from root
            if os.path.exists(dir):
                file_count = len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])
                print(file_count, "from", source['name'])