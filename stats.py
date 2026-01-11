import os
import argparse
from pathlib import Path
from src.airline_opp_codes import get_airline_codes

# Default Paths
DEFAULT_SCRAPER_DIR = Path(".")
DEFAULT_REPO_DIR = Path("../airline-logos")

# Mappings: Provider Name -> Subdirectory in both Scraper and Repo
# Note: FR24 Logos scraper directory is 'fr24_logos'
PROVIDERS = {
    "FlightAware Logos": "flightaware_logos",
    "RadarBox Banners": "radarbox_banners",
    "RadarBox Logos": "radarbox_logos",
    "FR24 Logos": "fr24_logos",
    "Avcodes Banners": "avcodes_banners",
}

def count_files(directory):
    if not directory.exists():
        return 0, set()
    files = {f.name for f in directory.glob("*.[pP][nN][gG]")}
    return len(files), files

def main():
    parser = argparse.ArgumentParser(description="Audit scraped assets against repository.")
    parser.add_argument("repo_path", nargs="?", default=str(DEFAULT_REPO_DIR), help="Path to airline-logos repo")
    args = parser.parse_args()

    repo_base = Path(args.repo_path)
    if not repo_base.exists():
        print(f"Error: Repository path not found: {repo_base}")
        return

    # Fetch source list
    print("Fetching master airline list (Wikipedia + FAA)...")
    all_airlines = get_airline_codes()
    source_icaos = set(a[1] for a in all_airlines)
    print(f"Master List: {len(source_icaos)} unique ICAO codes.\n")

    # Header
    # Local: In Scraper subdir
    # Repo: In Repo subdir
    # Net: Scraper - Repo
    # New: In Scraper but not Repo (To be synced)
    # Gap: In Repo but not Scraper (Missing from this run)
    # Legy: In Repo but NOT in Master List (Legacy data)
    # Fail: In Master List but NOT in Local (Scraper missed it)
    header = f"{'Provider':<20} | {'Local':>7} | {'Repo':>7} | {'Net':>7} | {'New':>7} | {'Gap':>7} | {'Legy':>7} | {'Fail':>7}"
    print(header)
    print("-" * len(header))

    totals = {k: 0 for k in ["local", "repo", "net", "new", "gap", "legy", "fail"]}

    for name, subdir in PROVIDERS.items():
        local_path = DEFAULT_SCRAPER_DIR / subdir
        repo_path = repo_base / subdir

        cnt_l, set_l = count_files(local_path)
        cnt_r, set_r = count_files(repo_path)

        # New: To be added to repo
        set_new = set_l - set_r
        cnt_new = len(set_new)

        # Gap: Exists in repo but missed in this run
        set_gap = set_r - set_l
        cnt_gap = len(set_gap)

        # Legacy: In Repo but not in Master List
        cnt_legy = 0
        for f in set_r:
            icao = Path(f).stem
            if icao not in source_icaos:
                cnt_legy += 1

        # Failed: In Master List but not in Local
        # (This is per provider, assumes provider *should* have everything)
        cnt_fail = 0
        for icao in source_icaos:
            if f"{icao}.png" not in set_l and f"{icao}.PNG" not in set_l:
                cnt_fail += 1

        net = cnt_l - cnt_r
        net_str = f"{net:+d}" if net != 0 else "0"

        print(f"{name:<20} | {cnt_l:>7} | {cnt_r:>7} | {net_str:>7} | {cnt_new:>7} | {cnt_gap:>7} | {cnt_legy:>7} | {cnt_fail:>7}")

        totals["local"] += cnt_l
        totals["repo"] += cnt_r
        totals["net"] += net
        totals["new"] += cnt_new
        totals["gap"] += cnt_gap
        totals["legy"] += cnt_legy
        totals["fail"] += cnt_fail

    print("-" * len(header))
    net_total_str = f"{totals['net']:+d}" if totals['net'] != 0 else "0"
    print(f"{'TOTAL':<20} | {totals['local']:>7} | {totals['repo']:>7} | {net_total_str:>7} | {totals['new']:>7} | {totals['gap']:>7} | {totals['legy']:>7} | {totals['fail']:>7}")
    print("\nNote: 'Fail' represents airlines in Master List missing from that specific provider's local folder.")

if __name__ == "__main__":
    main()
