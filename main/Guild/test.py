import asyncio
import aiohttp
import csv
import os
import re
import json

# ────────────────────────────────────────────────
# 설정
INPUT_FILE = "characters.csv"
OUTPUT_DIR = "logs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Player_data.csv")
ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s'
CONCURRENCY = 10  # 동시에 요청할 개수 제한

# ────────────────────────────────────────────────
# 비동기 HTTP 요청
async def fetch(session, method, url, **kwargs):
    """비동기 요청 + 예외처리"""
    try:
        async with session.request(method, url, **kwargs) as resp:
            if resp.status != 200:
                print(f"[WARN] {url} → HTTP {resp.status}")
                return None
            return await resp.text()
    except Exception as e:
        print(f"[ERROR] {url} 요청 실패:", e)
        return None


async def fetch_json(session, method, url, **kwargs):
    """JSON 응답용 fetch"""
    try:
        async with session.request(method, url, **kwargs) as resp:
            if resp.status != 200:
                print(f"[WARN] {url} → HTTP {resp.status}")
                return None
            return await resp.json()
    except Exception as e:
        print(f"[ERROR] {url} 요청 실패:", e)
        return None


# ────────────────────────────────────────────────
# 개별 데이터 수집 함수
async def get_ilvl(session, server, character):
    """공식 사이트 HTML에서 아이템 레벨 추출"""
    url = f"https://worldofwarcraft.com/ko-kr/character/{server}/{character}"
    html = await fetch(session, "GET", url)
    if not html:
        return "N/A"
    match = re.search(r'"averageItemLevel"\s*:\s*(\d+)', html)
    return match.group(1) if match else "N/A"


async def get_raiderio_score(session, server, character):
    """Raider.io API로 M+ 점수 추출"""
    url = "https://raider.io/api/v1/characters/profile"
    params = {
        "region": "kr",
        "realm": server,
        "name": character,
        "fields": "mythic_plus_scores_by_season:current"
    }
    data = await fetch_json(session, "GET", url, params=params)
    if not data:
        return "N/A"

    seasons = data.get("mythic_plus_scores_by_season", [])
    for season in seasons:
        if season.get("season") == "season-tww-3":
            return season.get("scores", {}).get("all", "N/A")
    return "N/A"


async def get_warcraftlogs_data(session, server, character):
    """WarcraftLogs GraphQL API"""
    url = "https://www.warcraftlogs.com/api/v2/client"
    query = {
        "query": f"""
        {{
          characterData {{
            character(name: "{character}", serverSlug: "{server}", serverRegion: "kr") {{
              name
              zoneRankings(metric: default)
            }}
          }}
        }}
        """
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = await fetch_json(session, "POST", url, json=query, headers=headers)
    try:
        return data["data"]["characterData"]["character"]["zoneRankings"]
    except (TypeError, KeyError):
        return None


# ────────────────────────────────────────────────
# 캐릭터 단위 크롤링
async def process_character(session, sem, row):
    async with sem:  # 동시 요청 제한
        server = row["Server"].strip()
        character = row["ID"].strip()

        print(f"▶ {character} ({server}) 처리 중...")

        ilvl, mplus_score, logs_data = await asyncio.gather(
            get_ilvl(session, server, character),
            get_raiderio_score(session, server, character),
            get_warcraftlogs_data(session, server, character),
        )

        # 개별 로그 저장
        log_file = os.path.join(OUTPUT_DIR, f"{character}_logs.txt")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs_data or {}, f, ensure_ascii=False, indent=2)

        return [character, ilvl, mplus_score]


# ────────────────────────────────────────────────
# 메인 실행
async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sem = asyncio.Semaphore(CONCURRENCY)

    # 입력 CSV 로드
    with open(INPUT_FILE, newline="", encoding="utf-8") as csvfile:
        reader = list(csv.DictReader(csvfile))

    async with aiohttp.ClientSession() as session:
        tasks = [process_character(session, sem, row) for row in reader]
        results = await asyncio.gather(*tasks)

    # 전체 요약 CSV 저장
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["캐릭터명", "아이템 레벨", "M+ 점수"])
        writer.writerows(results)

    print("\n=== ✅ 모든 크롤링 완료 ===")
    print(f"결과가 '{OUTPUT_FILE}' 에 저장되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())

