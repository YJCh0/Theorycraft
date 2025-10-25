import csv
import re
import requests

# Input Roster
input_file = "characters.csv"

results = []

print("Crawling Start")
with open(input_file, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        server = row['Server'].strip()
        character = row['ID'].strip()
        role = row['Role'].strip()
        spec = row['Class'].strip()
        
        url = f"https://worldofwarcraft.com/ko-kr/character/{server}/{character}"
        
        try:
            response = requests.get(url)
            html = response.text

            # ilvl crawl
            pattern = r'"averageItemLevel"\s*:\s*(\d+)'
            match = re.search(pattern, html)

            if match:
                ilvl = match.group(1)
            else:
                ilvl = "N/A"

            print(f"{character} => 아이템 레벨: {ilvl}")

        except Exception as e:
            print(f"{character} 처리 중 오류:", e)
            results.append([character, "오류"])
           
# Raider M+ Score
        url_raider = f"https://raider.io/api/v1/characters/profile"
        params = {
            "region": "kr",
            "realm": server,
            "name": character,
            "fields": "mythic_plus_scores_by_season:current"
        }
        
        response = requests.get(url_raider, params=params)
        data_raider = response.json()

        current_season_id = "season-tww-3"
        seasons = data_raider.get("mythic_plus_scores_by_season", [])

        current_season = None
        for season in seasons:
            if season.get("season") == current_season_id:
                current_season = season
                break
        
        if current_season:
            mythic_score = current_season.get("scores", {}).get("all", "N/A")
            print(f"Mythic+ : {mythic_score}")
            results.append([character, ilvl, mythic_score])

# Warcraftlogs Score

# Saving Files
output_file = "Player_data.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["캐릭터명", "아이템 레벨", "M+"])
    writer.writerows(results)

print(f"Crawling Done.")

