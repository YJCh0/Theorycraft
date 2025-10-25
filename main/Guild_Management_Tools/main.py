import csv
import re
import requests
import os

# ────────────────────────────────────────────────
# 설정
INPUT_FILE = "characters.csv"
OUTPUT_DIR = "logs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Player_data.csv")
ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s'

# ────────────────────────────────────────────────
# 유틸 함수
def safe_request(method, url, **kwargs):
    """requests 호출 및 예외 처리 + 상태 코드 확인"""
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {url} 요청 실패:", e)
        return None


def get_ilvl(server, character):
    """공식 사이트에서 아이템 레벨 추출"""
    url = f"https://worldofwarcraft.com/ko-kr/character/{server}/{character}"
    response = safe_request("GET", url)
    if not response:
        return "N/A"

    match = re.search(r'"averageItemLevel"\s*:\s*(\d+)', response.text)
    return match.group(1) if match else "N/A"


def get_raiderio_score(server, character):
    """Raider.io API로 M+ 점수 추출"""
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


def get_warcraftlogs_data(server, character):
    """WarcraftLogs GraphQL API에서 전투 로그 정보 추출"""
    url = "https://www.warcraftlogs.com/api/v2/client"
    query = f"""
    {{
      characterData {{
        character(name: "{character}", serverSlug: "{server}", serverRegion: "kr") {{
          name
          zoneRankings(metric: default)
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
        return "N/A"

    try:
        data = response.json()
        zone_rankings = data["data"]["characterData"]["character"]["zoneRankings"]
        return zone_rankings
    except (KeyError, TypeError):
        return None


# ────────────────────────────────────────────────
# Main Routine
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []

    print("=== Crawling Data ===")

    queue = 1
    with open(INPUT_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            server = row["Server"].strip()
            character = row["ID"].strip()
            role = row["Role"].strip()
            character_class = row["Class"].strip()

            roster_num = 20
            print(f"\n▶ Pending {character} ({server}) ...({queue}/{roster_num})")
            queue += 1

            print(f"  - Class: {character_class}")
            print(f"  - Role: {role}")
            ilvl = get_ilvl(server, character)
            print(f"  - ilvl: {ilvl}")

            mplus_score = get_raiderio_score(server, character)
            print(f"  - Mythic+: {mplus_score}")

            logs_data = get_warcraftlogs_data(server, character)
            if logs_data:
                print(f"  - Found Logs Data")
            else:
                print(f"  - No Logs Data")

            # Call API
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
            response = requests.post(url, json={'query': query}, headers=headers)
            res_json = response.json()


            character_info = res_json['data']['characterData']['character']
            zone_rankings = character_info.get('zoneRankings')
            # 개별 로그 파일 저장
            output_lines = []
            
            output_lines.append("WarcraftLogs Summary for")
            output_lines.append(f"  {character}")
            
            all_stars = zone_rankings.get('allStars')
            if all_stars and isinstance(all_stars, list) and len(all_stars) > 0:
                wcl_spec = all_stars[0].get('spec', 'unknown')
            else:
                wcl_spec = "unknown"

            output_lines.append(f"  {wcl_spec} {character_class}")

            healer_list = ["Restoration", "Holy", "Discipline", "Preservation", "Mistweaver"]
            # Overall Score
            if zone_rankings:
                output_lines.append(f"\nBest Performance Average: {zone_rankings.get('bestPerformanceAverage')}")
                output_lines.append("\nBest Performances:")
                for encounter in zone_rankings.get('rankings', []):
                    output_lines.append(f"  {encounter['encounter']['name']}, Score: {encounter.get('rankPercent')}")
            else:
                output_lines.append("\nCannot find Logs Data")

            results.append([character, ilvl, mplus_score, round(zone_rankings.get('bestPerformanceAverage', 'N/A'),2)])
            
            # AllStars Points
            if all_stars:
                output_lines.append("\nAll Stars Points:")
                for star in all_stars:
                    division = star.get('partition', {})
                    spec = star.get('spec', 'Unknown')
                    points = star.get('points', 0)
                    possible_points = star.get('possiblePoints', 0)
                    rank_percent = star.get('rankPercent', 'N/A')
                    output_lines.append(f"  Partition {division} | Spec: {spec} | Points: {points}/{possible_points} | Rank %: {rank_percent}")
            else:
                output_lines.append("\nCannot find All Star Points")
            
            # Ranking(%)
            ranking_percent = zone_rankings.get('rankings', [])
            if ranking_percent:
                if wcl_spec in healer_list:
                    output_lines.append("\nBoss HPS Percentage:")
                else:
                    output_lines.append("\nBoss DPS Percentage:")
                for encounter in ranking_percent:
                    boss = encounter.get('encounter', {}).get('name', 'Unknown')
                    percent = encounter.get('rankPercent', 0)
                    best = encounter.get('bestAmount', 0)
                    if wcl_spec in healer_list:
                        output_lines.append(f"  {boss}: Rank {percent}%, Best HPS {best}")
                    else:
                        output_lines.append(f"  {boss}: Rank {percent}%, Best DPS {best}")

            else:
                output_lines.append("\nCannot find Boss Ranking Data")
            
            # Ranking
            ranking = zone_rankings.get('allStars', [])
            if ranking:
                output_lines.append("\nRankings:")
                for partition in ranking:
                    division = partition.get('partition', {})
                    spec = partition.get('spec', 'Unknown')
                    ranks = partition.get('rank', 0)
                    region_ranks = partition.get('regionRank', 0)
                    server_ranks = partition.get('serverRank', 0)
                    output_lines.append(f"  Partition {division} | Spec: {spec} |  Rank: {ranks} | Region: {region_ranks} | Server: {server_ranks}")
            else:
                output_lines.append("\nCannot find Boss Data")

            # 텍스트 파일로 저장
            log_file = os.path.join(OUTPUT_DIR, f"{character}_logs.txt")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(output_lines))

    # 전체 요약 CSV 저장
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["캐릭터명", "ilvl", "M+ Score", "Logs"])
        writer.writerows(results)


    print("\n=== DONE ===")
    print(f"결과가 '{OUTPUT_FILE}'에 저장되었습니다.")


if __name__ == "__main__":
    main()

