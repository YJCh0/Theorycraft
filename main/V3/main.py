import requests
import csv
from rich.progress import Progress
import time
import os

# ────────────────────────────────────────────────
# Blizzard API Client Credentials
CLIENT_ID = "21d80d19190544d0bbe39c06c8af635d"
CLIENT_SECRET = "tEHJW0IkA76jRj680UVZ4hfqwaAB5JPp"
REGION = "kr"  # kr, us, eu 등
NAMESPACE = "profile-kr"  # 캐릭터/아이템 정보 조회용

# ────────────────────────────────────────────────
def get_access_token():
    """Blizzard API Client Credentials로 access token 발급"""
    url = f"https://{REGION}.battle.net/oauth/token"
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Access Token 발급 성공")
        return token
    else:
        print(f"❌ 토큰 발급 실패: {response.status_code} - {response.text}")
        return None

# ────────────────────────────────────────────────
def get_character_equipment(realm, character_name, token):
    """캐릭터 장비 정보 조회"""
    url = f"https://{REGION}.api.blizzard.com/profile/wow/character/{realm}/{character_name}/equipment"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": NAMESPACE, "locale": "ko_KR"}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {character_name} 장비 정보 조회 성공")
        return data
    else:
        print(f"❌ API 요청 실패: {response.status_code} - {response.text}")
        return None

# ────────────────────────────────────────────────
def process_character_name(character_name):
    """영어 이름은 소문자, 한글은 그대로 처리"""
    if any(ord(c) > 128 for c in character_name):  # 한글 처리
        return character_name
    else:  # 영어는 소문자로 변환
        return character_name.lower()

# ────────────────────────────────────────────────
def save_summary_markdown(results):
    """결과 요약을 Markdown 파일로 저장"""
    with open("summary.md", "w", encoding="utf-8") as f:
        headers = ["ID", "Role", "Class", "Average_ILVL"]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "---|" * len(headers) + "\n")
        
        for result in results:
            row = [
                result["ID"],
                result["Role"],
                result["Class"],
                str(result["Average_ILVL"])
            ]
            f.write("| " + " | ".join(row) + " |\n")

        # ✅ 파티 평균 아이템 레벨 추가
        if results:
            party_avg_ilvl = sum(r["Average_ILVL"] for r in results) / len(results)
            f.write("\n\n")
            f.write(f"### Average ilvl: **{party_avg_ilvl:.2f}**\n")

# ────────────────────────────────────────────────
def save_detailed_markdown(result):
    """개별 캐릭터의 장비 정보를 Markdown 파일로 저장"""
    file_name = f"detailed/{result['ID']}.md".replace(" ", "_")
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"# {result['ID']} - {result['Role']} - {result['Class']}\n\n")
        f.write("| Slot | Item Name | Item ILVL |\n")
        f.write("|------|-----------|-----------|\n")
        
        for item in result["Equipment"]:
            f.write(f"| {item['slot']} | {item['name']} | {item['ilvl']} |\n")

# ────────────────────────────────────────────────
def save_results_to_markdown(results):
    """결과를 Markdown 형식으로 저장"""
    with open("all_characters.md", "w", encoding="utf-8") as f:
        f.write("# Character Equipment Summary\n\n")
        
        for result in results:
            f.write(f"## {result['ID']} - {result['Role']} - {result['Class']}\n\n")
            f.write("| Slot | Item Name | Item ILVL |\n")
            f.write("|------|-----------|-----------|\n")
            
            for item in result["Equipment"]:
                f.write(f"| {item['slot']} | {item['name']} | {item['ilvl']} |\n")
            
            f.write("\n")  # 개별 캐릭터의 정보 간 구분을 위한 빈 줄

# ────────────────────────────────────────────────
def crawl_character_info(character_list, token):
    """캐릭터 정보 크롤링 진행 상태 표시"""
    with Progress() as progress:
        task = progress.add_task("[cyan]Crawling character data...", total=len(character_list))
        
        results = []  # 결과를 담을 리스트
        
        # 캐릭터 목록을 하나씩 처리하며 진행 상황 업데이트
        for character in character_list:
            equipment_data = get_character_equipment("azshara", character, token)  # 크롤링 실행
            
            if equipment_data:
                # 필요한 데이터만 필터링
                result = {"ID": character, "Role": "Tank", "Class": "Warrior", "Equipment": equipment_data}
                results.append(result)
            
            # 진행 상태 업데이트
            progress.update(task, advance=1)
        
    return results

def calculate_average_ilvl(equipment_info):
    filtered_items = [item for item in equipment_info if item['slot'] not in ['속옷', '겉옷']]

    if filtered_items:
        avg_ilvl = sum([item["ilvl"] for item in filtered_items]) / len(filtered_items)

        return round(avg_ilvl, 2)
    return 0


# ────────────────────────────────────────────────
def main():
    # 캐릭터 목록 불러오기 (characters.csv)
    characters = []
    with open('characters.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            characters.append(row)
    
    results = []
    
    token = get_access_token()
    if not token:
        return
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Crawling character data...", total=len(characters))
        
        for character in characters:
            character_name = process_character_name(character["ID"])  # 영어는 소문자, 한글은 그대로 처리
            equipment_data = get_character_equipment(character["Server"], character_name, token)
            
            if equipment_data:
                equipment_info = []
                for slot in equipment_data.get("equipped_items", []):
                    item = {
                        "slot": slot["slot"]["name"],
                        "name": slot["name"],
                        "ilvl": slot["level"]["value"],
                    }
                    equipment_info.append(item)
                
                # 평균 아이템 레벨 계산
                avg_ilvl = calculate_average_ilvl(equipment_info)
                result = {
                    "ID": character["ID"],
                    "Role": character["Role"],
                    "Class": character["Class"],
                    "Equipment": equipment_info,
                    "Average_ILVL": round(avg_ilvl, 2)
                }
                results.append(result)
                
                # 개별 캐릭터 상세 정보 저장
                save_detailed_markdown(result)
            
            # 진행 상태 업데이트
            progress.update(task, advance=1)

    # 요약 정보 저장
    save_summary_markdown(results)
    
    # 모든 결과를 Markdown으로 저장
    save_results_to_markdown(results)
    
    print("✅ 모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()

