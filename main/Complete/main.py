import requests
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.theme import Theme

# ────────────────────────────────────────────────
# API Keys / Client Credentials
BLIZZARD_CLIENT_ID = "21d80d19190544d0bbe39c06c8af635d"
BLIZZARD_CLIENT_SECRET = "tEHJW0IkA76jRj680UVZ4hfqwaAB5JPp"
WOWLOGS_API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s'
REGION = "kr"  # Blizzard region
NAMESPACE = "profile-kr"  # 캐릭터/아이템 정보 조회용

theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "error": "bold red",
    "warning": "yellow"
})
console = Console(theme=theme)

# ────────────────────────────────────────────────
def get_blizzard_token():
    url = f"https://{REGION}.battle.net/oauth/token"
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, data=data, auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET))
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ Blizzard 토큰 발급 실패: {response.status_code}")
        return None

# ────────────────────────────────────────────────
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

def get_character_equipment(realm, character_name, token):
    url = f"https://{REGION}.api.blizzard.com/profile/wow/character/{realm}/{character_name}/equipment"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": NAMESPACE, "locale": "ko_KR"}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json()
    return None

# ────────────────────────────────────────────────
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

# ────────────────────────────────────────────────
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
# ────────────────────────────────────────────────
def calculate_average_ilvl(equipment_info):
    filtered = [item for item in equipment_info if item['slot'] not in ['속옷', '겉옷']]
    if not filtered:
        return 0
    return round(sum([item["ilvl"] for item in filtered]) / len(filtered), 2)

# ────────────────────────────────────────────────
def process_character_name(name):
    return name.lower() if all(ord(c) < 128 for c in name) else name

# ────────────────────────────────────────────────
def save_detailed_markdown(result):
    os.makedirs("logs", exist_ok=True)
    file_name = f"logs/{result['ID']}.md".replace(" ", "_")
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"# {result['ID']} - {result['Role']} - {result['Class']}\n\n")
        f.write("| Slot | Item Name | Item ILVL |\n|------|-----------|-----------|\n")
        for item in result["Equipment"]:
            f.write(f"| {item['slot']} | {item['name']} | {item['ilvl']} |\n")
        f.write(f"\n**Raider.IO Score:** {result['RaiderIO']}\n\n")

        wcl = result.get("WCL")
        if wcl:
            f.write(f"## WarcraftLogs Summary for\n  {result['ID']}\n  {result['Class']}\n\n")
            f.write(f"**Best Performance Average:** {wcl['BestPerformanceAverage']}\n\n")
            f.write("### Best Performances:\n")
            for boss in wcl["BestPerformances"]:
                f.write(f"  {boss['Boss']}, Score: {boss['Score']}\n")
            f.write("\n### All Stars Points:\n")
            for star in wcl["AllStars"]:
                f.write(f"  Partition {star['Partition']} | Spec: {star['Spec']} | Points: {star['Points']} | Rank %: {star['RankPercent']}\n")
            f.write("\n### Boss DPS Percentage:\n")
            for boss in wcl["BossDPS"]:
                f.write(f"  {boss['Boss']}: Rank {boss['RankPercent']}%, Best DPS {boss['BestDPS']}\n")
            f.write("\n### Rankings:\n")
            for rank in wcl["Rankings"]:
                f.write(f"  Partition {rank['Partition']} | Spec: {rank['Spec']} | Rank: {rank['Rank']} / {rank['OutOf']} | Region: {rank['Region']} | Server: {rank['Server']}\n")

# ────────────────────────────────────────────────
def save_summary_markdown(results):
    with open("summary.md", "w", encoding="utf-8") as f:
        headers = ["ID", "Role", "Class", "Average_ILVL", "RaiderIO"]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "---|" * len(headers) + "\n")
        for r in results:
            row = [r["ID"], r["Role"], r["Class"], str(r["Average_ILVL"]), str(r["RaiderIO"])]
            f.write("| " + " | ".join(row) + " |\n")
        if results:
            party_avg_ilvl = sum(r["Average_ILVL"] for r in results) / len(results)
            f.write(f"\n### Average ilvl: **{party_avg_ilvl:.2f}**\n")

# ────────────────────────────────────────────────
# Summary & Weekly Comparison
def print_console_summary(results):
    table = Table(title="WoW Character Summary", show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Class", style="magenta")
    table.add_column("Spec", style="yellow")
    table.add_column("ilvl", justify="right", style="green")
    table.add_column("M+", justify="right", style="blue")
    table.add_column("WCL", justify="right", style="red")

    il, mp, wc = 0, 0, 0
    for r in results:
        table.add_row(*[str(x) for x in r])
        try: il += int(r[3]); mp += float(r[4].replace(",", "")); wc += float(r[5].replace(",", ""))
        except: pass
    console.print(table)

    if len(results):
        console.print(f"[info]Average ilvl: {il/len(results):.1f} | M+: {mp/len(results):.1f} | WCL: {wc/len(results):.1f}[/info]")

def main():
    characters = []
    with open("characters.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            characters.append(row)

    token = get_blizzard_token()
    if not token:
        return

    results = []
    with Progress() as progress:
        task = progress.add_task("[cyan]Crawling character data...", total=len(characters))
        for char in characters:
            name = process_character_name(char["ID"])
            equipment_data = get_character_equipment(char["Server"], name, token)
            equipment_info = []
            if equipment_data:
                for slot in equipment_data.get("equipped_items", []):
                    equipment_info.append({
                        "slot": slot["slot"]["name"],
                        "name": slot["name"],
                        "ilvl": slot["level"]["value"]
                    })
            avg_ilvl = calculate_average_ilvl(equipment_info)
            raiderio = get_raiderio_score(char["Server"], name)
            wcl = get_wcl_score(char["Server"], name)
            result = {
                "ID": char["ID"],
                "Role": char["Role"],
                "Class": char["Class"],
                "Equipment": equipment_info,
                "Average_ILVL": avg_ilvl,
                "RaiderIO": raiderio,
                "WCL": wcl
            }
            results.append(result)
            save_detailed_markdown(result)
            progress.update(task, advance=1)

    save_summary_markdown(results)
    print("Done!")
    print_console_summary(results)
    
if __name__ == "__main__":
    main()

