import requests
import re
from config import WCL_ACCESS_TOKEN

# ────────────────────────────────────────────────
# 공통 유틸
# ────────────────────────────────────────────────
def safe_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {url} 요청 실패:", e)
        return None


# ────────────────────────────────────────────────
# 공식 사이트 ilvl
# ────────────────────────────────────────────────
def get_ilvl(server, character):
    url = f"https://worldofwarcraft.com/ko-kr/character/{server}/{character}"
    response = safe_request("GET", url)
    if not response:
        return "N/A"
    match = re.search(r'"averageItemLevel"\s*:\s*(\d+)', response.text)
    return match.group(1) if match else "N/A"


# ────────────────────────────────────────────────
# Raider.io M+ 점수
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
        if season.get("season") == "season-tww-3":
            return season.get("scores", {}).get("all", "N/A")
    return "N/A"


# ────────────────────────────────────────────────
# WarcraftLogs API
# ────────────────────────────────────────────────
def get_warcraftlogs_data(server, character, role="dps"):
    metric_type = "hps" if role.lower() == "healer" else "dps"

    query = f"""
    {{
      characterData {{
        character(name: "{character}", serverSlug: "{server}", serverRegion: "kr") {{
          name
          zoneRankings(metric: {metric_type}) {{
            bestPerformanceAverage
            rankings {{
              encounter {{ name }}
              spec
              bestAmount
              rankPercent
              outOf
            }}
          }}
        }}
      }}
    }}
    """

    headers = {
        "Authorization": f"Bearer {WCL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = safe_request("POST", "https://www.warcraftlogs.com/api/v2/client",
                            json={'query': query}, headers=headers)
    if not response:
        return {"error": "WCL API 호출 실패"}

    data = response.json()
    if "errors" in data:
        return {"error": data["errors"][0]["message"]}

    try:
        char = data["data"]["characterData"]["character"]
        return char["zoneRankings"]
    except (KeyError, TypeError):
        return {"error": "데이터를 찾을 수 없음"}


# ────────────────────────────────────────────────
# Guild 전체 요약 (WCL Public API)
# ────────────────────────────────────────────────
def get_guild_summary(guild_name, server):
    """길드 내 전체 캐릭터 로그 요약"""
    query = f"""
    {{
      guildData {{
        guild(name: "{guild_name}", serverSlug: "{server}", serverRegion: "kr") {{
          name
          zoneRankings(metric: dps)
        }}
      }}
    }}
    """

    headers = {
        "Authorization": f"Bearer {WCL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = safe_request("POST", "https://www.warcraftlogs.com/api/v2/client",
                            json={'query': query}, headers=headers)
    if not response:
        return {"error": "WCL API 호출 실패"}

    data = response.json()
    try:
        guild = data["data"]["guildData"]["guild"]
        return guild["zoneRankings"]
    except (KeyError, TypeError):
        return {"error": "데이터를 찾을 수 없음"}

