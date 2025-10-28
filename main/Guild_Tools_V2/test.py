import csv
import re
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.theme import Theme
from rich.table import Table

# ────────────────────────────────────────────────
# Settings
INPUT_FILE = "characters.csv"
OUTPUT_DIR = "logs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Player_data.csv")
FAILED_LOG = os.path.join(OUTPUT_DIR, "failed_characters.log")
PREVIOUS_FILE = os.path.join(OUTPUT_DIR, "previous_Player_data.csv")
WEEKLY_FILE = os.path.join(OUTPUT_DIR, "weekly_comparison.csv")
ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s'

# Console Style
theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "error": "bold red",
    "warning": "yellow"
})
console = Console(theme=theme)

# ────────────────────────────────────────────────
# Functions
def safe_request(method, url, retries=3, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                time.sleep(1.5)
            else:
                console.print(f"[error]❌ Error ({url}): {e}[/error]")
                return None

def format_amount(value):
    if value is None or value == "N/A":
        return "None"
    try:
        return f"{float(value):,.1f}"
    except:
        return str(value)

def format_rank(value):
    if value is None or value == 0 or value == "N/A":
        return "N/A"
    try:
        return f"{int(round(value)):,}"
    except:
        return str(value)

def format_amount_int(value):
    if value is None or value == "N/A":
        return "None"
    try:
        return f"{int(round(value)):,}"
    except:
        return str(value)

def get_ilvl(server, character):
    url = f"https://worldofwarcraft.com/ko-kr/character/{server}/{character}"
    response = safe_request("GET", url)
    if not response:
        return 0
    match = re.search(r'"averageItemLevel"\s*:\s*(\d+)', response.text)
    return int(match.group(1)) if match else 0

def get_raiderio_score(server, character):
    url = "https://raider.io/api/v1/characters/profile"
    params = {
        "region": "kr",
        "realm": server,
        "name": character,
        "fields": "mythic_plus_scores_by_season:current"
    }
    response = safe_request("GET", url, params=params)
    if not response:
        return "N/A"
    data = response.json()
    seasons = data.get("mythic_plus_scores_by_season", [])
    for season in seasons:
        if "season-tww-3" in season.get("season", ""):
            return season.get("scores", {}).get("all", "N/A")
    return "N/A"

def get_wcl_score(server, character, role):
    url = "https://www.warcraftlogs.com/api/v2/client"
    metric_type = "hps" if role.lower() == "healer" else "dps"
    query = f"""
    {{
      characterData {{
        character(name: "{character}", serverSlug: "{server}", serverRegion: "kr") {{
          name
          zoneRankings(metric: {metric_type})
        }}
      }}
    }}
    """
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = safe_request("POST", url, json={'query': query}, headers=headers)
    if not response:
        return None

    try:
        data = response.json()
        character_info = data['data']['characterData']['character']
        return character_info.get('zoneRankings', {})
    except (KeyError, TypeError):
        return None

def write_failed_log(character, reason="데이터 수집 실패"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(FAILED_LOG, "a", encoding="utf-8") as f:
        f.write(f"{character}: {reason}\n")

def format_wcl_log(character, character_class, wcl_spec, wcl_data, role):
    lines = []
    lines.append("WarcraftLogs Summary for")
    lines.append(f"  {character}")
    lines.append(f"  {wcl_spec} {character_class}\n")

    best_perf_avg = wcl_data.get('bestPerformanceAverage', None)
    lines.append(f"Best Performance Average: {format_amount(best_perf_avg)}\n")

    # Best Performances
    lines.append("Best Performances:")
    rankings = wcl_data.get('rankings', [])
    if rankings:
        for encounter in rankings:
            boss_name = encounter.get('encounter', {}).get('name', 'Unknown')
            score = encounter.get('rankPercent')
            lines.append(f"  {boss_name}, Score: {format_amount(score)}")
    else:
        lines.append("  Cannot find Best Performances")
    lines.append("")

    # All Stars
    lines.append("All Stars Points:")
    all_stars = wcl_data.get('allStars', [])
    if all_stars:
        for star in all_stars:
            division = star.get('partition', 'N/A')
            spec = star.get('spec', 'Unknown')
            points = star.get('points', 0)
            possible = star.get('possiblePoints', 0)
            rank_percent = star.get('rankPercent', 0)
            lines.append(
                f"  Partition {division} | Spec: {spec} | Points: {format_amount(points)}/{format_amount(possible)} | Rank %: {format_amount(rank_percent)}"
            )
    else:
        lines.append("  Cannot find All Stars Points")
    lines.append("")

    # Boss DPS/HPS
    lines.append("\nBoss HPS Percentage:" if role.lower() == "healer" else "\nBoss DPS Percentage:")
    if rankings:
        for encounter in rankings:
            boss_name = encounter.get('encounter', {}).get('name', 'Unknown')
            rank_percent = encounter.get('rankPercent')
            best_amount = encounter.get('bestAmount', 0)
            lines.append(
                f"  {boss_name}: Rank {format_amount(rank_percent)}%, Best {'HPS' if role.lower()=='healer' else 'DPS'} {format_amount_int(best_amount)}"
            )
    else:
        lines.append("  Cannot find Boss Rankings")

    # Rankings
    lines.append("\nRankings:")
    if all_stars:
        for partition in all_stars:
            division = partition.get('partition', 'N/A')
            spec = partition.get('spec', 'Unknown')
            rank = partition.get('rank', 0)
            total = partition.get('total', 0)
            region_rank = partition.get('regionRank', 0)
            server_rank = partition.get('serverRank', 0)
            lines.append(
                f"  Partition {division} | Spec: {spec} | Rank: {format_rank(rank)} / {format_rank(total)} | Region: {format_rank(region_rank)} | Server: {format_rank(server_rank)}"
            )
    else:
        lines.append("  Cannot find Rankings")

    return "\n".join(lines)

def crawl_character(row, queue, roster_num, attempt=1):
    server = row["Server"].strip()
    character = row["ID"].strip()
    role = row["Role"].strip()
    character_class = row["Class"].strip()

    console.print(f"[info]▶ Fetching {character} ... (Attempt: {attempt})[/info]")

    ilvl = get_ilvl(server, character)
    mplus_score = get_raiderio_score(server, character)
    wcl_data = get_wcl_score(server, character, role)

    if not wcl_data or (ilvl == 0 and mplus_score == "N/A"):
        if attempt < 3:
            time.sleep(2)
            return crawl_character(row, queue, roster_num, attempt + 1)
        console.print(f"[error]❌ {character} Failed Crawling — Reported in [/error]")
        write_failed_log(character)
        return [character, character_class, "N/A", 0, "N/A", "N/A"]

    all_stars = wcl_data.get('allStars') if wcl_data else []
    wcl_spec = all_stars[0].get('spec', 'unknown') if all_stars else "unknown"

    # Writing Logs files
    log_content = format_wcl_log(character, character_class, wcl_spec, wcl_data, role)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, f"{character}_logs.txt"), "w", encoding="utf-8") as f:
        f.write(log_content)

    console.print(f"[success]✔ {character} Complete! ({wcl_spec} {character_class}, ilvl {ilvl})[/success]")

    best_perf_avg = wcl_data.get('bestPerformanceAverage')
    best_perf_avg_formatted = f"{best_perf_avg:.2f}" if best_perf_avg else "None"

    return [character, character_class, wcl_spec, ilvl, format_amount(mplus_score), best_perf_avg_formatted]

def generate_weekly_comparison(current_file, previous_file, output_file):
    current_data = {}
    with open(current_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            current_data[row["ID"]] = row

    previous_data = {}
    if os.path.exists(previous_file):
        with open(previous_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                previous_data[row["ID"]] = row

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["ID", "Class", "Spec", "ilvl", "ilvl_change", "M+", "M+_change", "WCL", "WCL_change"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for char_id, curr in current_data.items():
            prev = previous_data.get(char_id, {})
            ilvl_change = (int(curr["ilvl"]) - int(prev.get("ilvl", curr["ilvl"]))) if prev else 0
            mplus_change = (float(curr["M+"].replace(",", "")) - float(prev.get("M+", curr["M+"]).replace(",", ""))) if prev else 0
            wcl_change = (float(curr["WCL"]) - float(prev.get("WCL", curr.get("WCL")))) if prev else 0

            writer.writerow({
                "ID": char_id,
                "Class": curr["Class"],
                "Spec": curr["Spec"],
                "ilvl": curr["ilvl"],
                "ilvl_change": ilvl_change,
                "M+": curr["M+"],
                "M+_change": mplus_change,
                "WCL": curr["WCL"],
                "WCL_change": wcl_change
            })

    console.print(f"[success]✅ Weekly comparison saved to {output_file}[/success]")
    os.replace(current_file, previous_file)
    console.print(f"[info]📦 Previous week data updated: {previous_file}[/info]")

# ────────────────────────────────────────────────
# Main
def main():
    characters = []
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        characters = list(reader)

    results = []
    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Processing Characters...", total=len(characters))
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(crawl_character, char, results, idx+1) for idx, char in enumerate(characters)]
            for future in futures:
                res = future.result()
                if res:
                    results.append(res)
                progress.advance(task)

    # Save CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Class", "Spec", "ilvl", "M+", "WCL"])
        writer.writerows(results)

    console.print(f"[success]✅ Character data saved to {OUTPUT_FILE}[/success]")

    # Weekly Comparison
    generate_weekly_comparison(OUTPUT_FILE, PREVIOUS_FILE, WEEKLY_FILE)

if __name__ == "__main__":
    main()

