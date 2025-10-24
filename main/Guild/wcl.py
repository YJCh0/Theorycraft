import requests

# Access Token
access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s'

# GraphQL Endpoint
url = 'https://www.warcraftlogs.com/api/v2/client'

character_name = "죽탄야"
character_server = "azshara"
character_region = "kr"

# GraphQL Query
query =f""" 
{{
  characterData {{
    character(name: "{character_name}", serverSlug: "{character_server}", serverRegion: "{character_region}") {{
      name
      zoneRankings(metric: default)
      }}
    }}
}}
"""

# Header Settings
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Call API
response = requests.post(url, json={'query': query}, headers=headers)
res_json = response.json()

character = res_json['data']['characterData']['character']
zone_rankings = character.get('zoneRankings')

# 결과를 담을 문자열 리스트
output_lines = []

output_lines.append("WarcraftLogs Summary for")
output_lines.append(f"{character_name}")

# Overall Score
if zone_rankings:
    output_lines.append(f"\nBest Performance Average: {zone_rankings.get('bestPerformanceAverage')}")
    output_lines.append("\nBest Performances:")
    for encounter in zone_rankings.get('rankings', []):
        output_lines.append(f"  {encounter['encounter']['name']}, Score: {encounter.get('rankPercent')}")
else:
    output_lines.append("\nCannot find Logs Data")

# AllStars Points
all_stars = zone_rankings.get('allStars')
if all_stars:
    output_lines.append("\nAll Stars Points:")
    for star in all_stars:
        division = star.get('partition', {})
        spec = star.get('spec', 'Unknown')
        points = star.get('points', 0)
        possible_points = star.get('possiblePoints', 0)
        rank_percent = star.get('rankPercent', 'N/A')
        output_lines.append(f"  Partition{division} | Spec: {spec} | Points: {points}/{possible_points} | Rank %: {rank_percent}")
else:
    output_lines.append("\nCannot find All Star Points")

# Ranking(%)
ranking_percent = zone_rankings.get('rankings', [])
if ranking_percent:
    output_lines.append("\nBoss DPS Percentage:")
    for encounter in ranking_percent:
        boss = encounter.get('encounter', {}).get('name', 'Unknown')
        percent = encounter.get('rankPercent', 0)
        best = encounter.get('bestAmount', 0)
        output_lines.append(f"  {boss}: Rank {percent}%, Best DPS {best}")
else:
    output_lines.append("\nCannot find Boss Data")

# Ranking
ranking = zone_rankings.get('allStars', [])
if ranking:
    output_lines.append("\nRankings:")
    for partition in ranking:
        division = partition.get('partition', {})
        ranks = partition.get('rank', 0)
        region_ranks = partition.get('regionRank', 0)
        server_ranks = partition.get('serverRank', 0)
        output_lines.append(f"  Partition{division} |  Rank {ranks} | Region {region_ranks} | Server {server_ranks}")
else:
    output_lines.append("\nCannot find Boss Data")

# 텍스트 파일로 저장
with open('warcraftlogs_summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("Results saved to warcraftlogs_summary.txt")

