import os
import requests
from PIL import Image
from io import BytesIO
import threading
import time
from airline_opp_codes import get_airline_codes
from PIL import ImageChops
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


for source in sources:
    name = source['name']
    print(f'Would you like {name}: Y/N')
    source['enable'] = input().strip().upper() == 'Y'
    if source['enable']:
        source_folder = os.path.join("./", source['dir'])
        os.makedirs(source_folder, exist_ok=True)




def is_blank(img):
    # Compare the image with a blank image of the same size
    blank = Image.new(img.mode, img.size, img.getpixel((0, 0)))
    diff = ImageChops.difference(img, blank)
    if not diff.getbbox():
        return True  # The image is blank
    return False  # The image is not blank

def images_are_same(img1, img2):
    # Check if images have the same size and mode
    if img1.size != img2.size or img1.mode != img2.mode:
        return False  # The images are different

    # Compare two images to see if they are the same
    diff = ImageChops.difference(img1, img2)
    if not diff.getbbox():
        return True  # The images are the same
    return False  # The images are different


def save_pic(url, logo_file_path, source, icao_code):
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        if img.size != (1, 1) and not is_blank(img):  # Check for 1x1 and blank image
            if source == RB_LOGOS:
                placeholder_img = Image.open('RB_PLACERHOLDER.png')
                if images_are_same(img, placeholder_img):
                    print(f"Placeholder image received for {icao_code} from {source}, not saved.")
                    return
            img.save(logo_file_path)
            print(f"Downloaded {icao_code} from {source}")
        else:
            print(f"Placeholder or blank image received for {icao_code} from {source}, not saved.")
    else:
        print(response.status_code, "for", icao_code, source)

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
        return f"https://images.flightradar24.com/assets/airlines/logotypes/{self.iata_code}_{self.icao_code}.png"

    @property
    def rb_banner_download_url(self):
        return f"https://cdn.radarbox.com/airlines/{self.icao_code}.png"

    @property
    def rb_logo_download_url(self):
        return f"https://cdn.radarbox.com/airlines/sq/{self.icao_code}.png"




max_threads = 10  # Set your desired max threads here
semaphore = threading.Semaphore(max_threads)

# Shared counter for completed tasks
completed_counter = 0
counter_lock = threading.Lock()  # Lock to synchronize access to the counter

def print_progress():
    global completed_counter  # Corrected keyword
    with counter_lock:
        completed_counter += 1
        percent_complete = (completed_counter / len(airline_codes)) * 100
        print(f'Progress: {percent_complete:.2f}%')

use_wiki_airlines = True
if use_wiki_airlines:
    # Global set to keep track of processed ICAO codes
    processed_icao_codes = set()
    processing_lock = threading.Lock()

    def download_logo(code):
        global processed_icao_codes
        with processing_lock:
            if code.icao_code in processed_icao_codes:
                return  # Skip if the code has already been processed
            processed_icao_codes.add(code.icao_code)
            # ... rest of your download_logo function ...
            if code.icao_code:
                for source in sources:
                    if source['enable']:
                        logo_file_path = os.path.join(source['dir'], f"{code.icao_code}.png")
                        if source['name'] == FA_LOGOS:
                            url = code.flightaware_logo_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == RB_BANNERS:
                            url = code.rb_banner_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == RB_LOGOS:
                            url = code.rb_logo_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == FR24_LOGOS:
                            if code.iata_code:
                                url = code.fr24_banner_download_url
                                save_pic(url, logo_file_path, source['name'], code.icao_code)
                        elif source['name'] == AVCODES_UK_BANNERS:
                            url = code.avcodes_uk_banner_download_url
                            save_pic(url, logo_file_path, source['name'], code.icao_code)
                time.sleep(0.5)

    # Your existing code for threading
    airline_codes = get_airline_codes()
    for airline in airline_codes:
        iata = airline[0]
        icao = airline[1]
        code = AirlineCode(iata, icao)
        semaphore.acquire()  # Decrease the counter or block if the counter is 0
        t = threading.Thread(target=download_logo, args=(code,))
        t.start()

        def release_semaphore(thread, semaphore):
            thread.join()
            semaphore.release()  # Increase the counter
            print_progress()  # Print progress after each task

        threading.Thread(target=release_semaphore, args=(t, semaphore)).start()

for source in sources:
    if source['enable']:
        # Count the number of files
        dir = source['dir']
        file_count = len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])
        print(file_count, "from", source['name'])