import csv
import re
import requests
import os
from concurrent.futures import ThreadPoolExecutor

# ────────────────────────────────────────────────
# 설정
INPUT_FILE = "characters.csv"
OUTPUT_DIR = "logs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Player_data.csv")
ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s'

# ────────────────────────────────────────────────
# 유틸 함수
def safe_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {url} 요청 실패:", e)
        return None

def format_amount(value):
    """M+ 점수 및 퍼센트: 소숫점 1자리"""
    if value is None or value == "N/A":
        return "None"
    try:
        return f"{float(value):,.1f}"
    except:
        return str(value)

def format_rank(value):
    """등수: INTEGER, 0이면 N/A"""
    if value is None or value == 0 or value == "N/A":
        return "N/A"
    try:
        return f"{int(round(value)):,}"
    except:
        return str(value)

def format_amount_int(value):
    """Boss DPS/HPS: INTEGER"""
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
        if season.get("season") == "season-tww-3":
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

# ────────────────────────────────────────────────
def crawl_character(row, queue, roster_num):
    server = row["Server"].strip()
    character = row["ID"].strip()
    role = row["Role"].strip()
    character_class = row["Class"].strip()

    print(f"\n▶ Pending {character} ({server}) ...({queue}/{roster_num})")

    ilvl = get_ilvl(server, character)
    mplus_score = get_raiderio_score(server, character)
    wcl_data = get_wcl_score(server, character, role)

    output_lines = []
    output_lines.append("WarcraftLogs Summary for")
    output_lines.append(f"  {character}")

    # Spec 추출
    all_stars = wcl_data.get('allStars') if wcl_data else []
    if all_stars and isinstance(all_stars, list) and len(all_stars) > 0:
        wcl_spec = all_stars[0].get('spec', 'unknown')
    else:
        wcl_spec = "unknown"

    output_lines.append(f"  {wcl_spec} {character_class}")

    # Best Performance Average
    best_perf_avg = wcl_data.get('bestPerformanceAverage') if wcl_data else None
    output_lines.append(f"\nBest Performance Average: {format_amount(best_perf_avg) if best_perf_avg is not None else 'None'}")

    # Best Performances
    output_lines.append("\nBest Performances:")
    if wcl_data and wcl_data.get('rankings'):
        for encounter in wcl_data['rankings']:
            boss_name = encounter.get('encounter', {}).get('name', 'Unknown')
            score = encounter.get('rankPercent')
            output_lines.append(f"  {boss_name}, Score: {format_amount(score) if score is not None else 'None'}")
    else:
        output_lines.append("  Cannot find Best Performances")

    # All Stars Points
    output_lines.append("\nAll Stars Points:")
    if all_stars:
        for star in all_stars:
            division = star.get('partition', {})
            spec = star.get('spec', 'Unknown')
            points = star.get('points', 0)
            possible_points = star.get('possiblePoints', 0)
            rank_percent = star.get('rankPercent', 'N/A')
            output_lines.append(f"  Partition {division} | Spec: {spec} | Points: {format_amount(points)}/{format_amount(possible_points)} | Rank %: {format_amount(rank_percent)}")
    else:
        output_lines.append("  Cannot find All Stars Points")

    # Boss DPS/HPS
    output_lines.append("\nBoss HPS Percentage:" if role.lower() == "healer" else "\nBoss DPS Percentage:")
    if wcl_data and wcl_data.get('rankings'):
        for encounter in wcl_data['rankings']:
            boss_name = encounter.get('encounter', {}).get('name', 'Unknown')
            rank_percent = encounter.get('rankPercent')
            best_amount = encounter.get('bestAmount', 0)
            output_lines.append(f"  {boss_name}: Rank {format_amount(rank_percent)}%, Best {'HPS' if role.lower()=='healer' else 'DPS'} {format_amount_int(best_amount)}")
    else:
        output_lines.append("  Cannot find Boss Rankings")

    # Rankings
    output_lines.append("\nRankings:")
    if all_stars:
        for partition in all_stars:
            division = partition.get('partition', {})
            spec = partition.get('spec', 'Unknown')
            rank = partition.get('rank', 0)
            region_rank = partition.get('regionRank', 0)
            server_rank = partition.get('serverRank', 0)
            total = partition.get('total', 0)
            output_lines.append(
                f"  Partition {division} | Spec: {spec} | "
                f"Rank: {format_rank(rank)} / {format_rank(total)} | "
                f"Region: {format_rank(region_rank)} | "
                f"Server: {format_rank(server_rank)}"
            )
    else:
        output_lines.append("  Cannot find Rankings")

    # Save to txt
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_file = os.path.join(OUTPUT_DIR, f"{character}_logs.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(output_lines))

    # CSV 반환 (Spec 추가됨)
    return [character, character_class, wcl_spec, ilvl, format_amount(mplus_score), format_amount(best_perf_avg) if best_perf_avg else "None"]

# ────────────────────────────────────────────────
def main():
    results = []
    with open(INPUT_FILE, newline="", encoding="utf-8") as csvfile:
        reader = list(csv.DictReader(csvfile))
        roster_num = len(reader)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(crawl_character, row, i+1, roster_num) for i, row in enumerate(reader)]
            for future in futures:
                results.append(future.result())

    # Save to CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Class", "Spec", "ilvl", "M+", "WCL"])
        for row in results:
            writer.writerow(row)

    print("\n=== DONE ===")

# ────────────────────────────────────────────────
if __name__ == "__main__":
    main()

