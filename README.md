# Airline Logo Scraper

A robust Python tool to scrape and organize airline logos and banners from multiple aviation data sources.

### Example Output
- **Image Repository**: [Jxck-S/airline-logos](https://github.com/Jxck-S/airline-logos)
- **Live Gallery**: [View Logos & Banners](https://jxck-s.github.io/airline-logos/)

## Features

- **Multi-Source Scraping**: Downloads logos and banners from:
  - **FlightAware** (Logos)
  - **FlightRadar24** (Banners - Scraped from Index)
  - **RadarBox** (Logos & Banners)
  - **Avcodes UK** (Banners)
- **Enhanced Coverage**: Combines airline codes from **Wikipedia** and **FAA** (Chapter 3) for maximum coverage (>8,000 airlines).
- **Smart Filtering**: 
  - Detects and skips blank or placeholder images.
  - Dedupes identical images.
- **Performance**: 
  - Uses `ThreadPoolExecutor` for concurrent downloads.
  - Configurable threads and delays.
- **User Friendly**:
  - **Sticky Progress Footer**: Shows live "Session" (New) vs "Total" (Directory) counts.

  - Interactive or Automatic (`-A`) modes.

## Project Structure

- `main.py`: The entry point for the scraper.
- `src/`: Contains the core logic (`airline_logos.py`, scrapers, etc.).

## Installation

### Prerequisites
- Python 3.9+

### Using Pipenv (Recommended)
This project uses [Pipenv](https://pipenv.pypa.io/en/latest/) for dependency management.

```bash
# Install dependencies and create virtual environment
pipenv install
```

### Using pip
Alternatively, you can use standard `pip` with `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Usage

### Scraper (`main.py`)

**Interactive Mode**: Run without arguments to selectively enable sources.
```bash
python3 main.py
```

**Automatic Mode**: Download from all sources without prompting.
```bash
python3 main.py -A
```

**Performance Tuning**:
Customize threading and delays to speed up large scrapes or avoid rate limits.
```bash
# 20 threads, 0.1s delay, skip existing files (-s)
python3 main.py -A -s -t 20 -d 0.1
```

**Options**:
- `-A, --all`: Enable all sources.
- `-s, --skip`: Skip files that already exist (checks filename).
- `-t, --threads`: Number of concurrent download threads (Default: 10).
- `-d, --delay`: Delay between requests per thread (Default: 0.5s).
- `--fr24-method`: `scrape` (Default, recommended) or `brute` (Legacy guessing).



## Progress Display

When running `main.py`, the sticky footer provides real-time insights:

```
NEW DURING skip FA:5 | RB Ban:0 ...   <-- Files downloaded in this specific session
TOTAL DIR+NEW FA:1320 | RB Ban:1115 ... <-- Total files in your library
Progress: 568/7674 (7.40%)            <-- Overall progress through the airline list
```

## Disclaimer

This tool is for educational purposes only. Please respect the terms of service and usage rights of the respective websites.

## Future Possibilities

Potential new sources for expanded coverage:

- **TripAdvisor**: [Airlines Page](https://www.tripadvisor.com/Airlines)
  - Example: `https://static.tacdn.com/img2/flights/airlines/logos/100x100/AeroMexico.png`
  - *Note: Would require name-to-ICAO mapping via regex/lookup.*
- **Google Flights**:
  - Example: `https://www.gstatic.com/flights/airline_logos/70px/NH.png`
  - *Note: Uses IATA codes (e.g. NH for ANA). Would require IATA-to-ICAO mapping.*
