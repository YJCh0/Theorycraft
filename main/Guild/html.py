import re
import json
import requests

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.1 Safari/537.36"
    )
}

# ⚠️ 반드시 "blizzard.com" + "/kr/" 포함
url = "https://worldofwarcraft.blizzard.com/ko-kr/character/kr/azshara/전사잠탱이"

response = requests.get(url, headers=headers)
html = response.text

# HTML을 파일로 저장해 직접 눈으로 확인해보세요
with open("wow_test.html", "w", encoding="utf-8") as f:
    f.write(html)

match = re.search(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html
)

if not match:
    print("❌ JSON 데이터(script id='__NEXT_DATA__')를 찾을 수 없습니다.")
else:
    data = json.loads(match.group(1))
    char_data = data["props"]["pageProps"]["character"]

    print(f"이름: {char_data['name']}")
    print(f"직업: {char_data['class']['name']}")
    print(f"특성: {char_data['active_spec']['name']}")
    print(f"아이템 레벨: {char_data['averageItemLevel']}")

