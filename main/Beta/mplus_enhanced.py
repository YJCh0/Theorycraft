import requests
import json
import os
import time
from datetime import datetime

REGION = os.getenv("REGION", "kr")

def get_character_recent_mplus(server, character):
    """Get recent M+ runs (instead of best runs)"""
    url = "https://raider.io/api/v1/characters/profile"
    params = {
        "region": REGION,
        "realm": server,
        "name": character,
        "fields": "mythic_plus_scores_by_season:current,mythic_plus_recent_runs,gear"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️ API returned {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def format_duration(seconds):
    """Convert seconds to MM:SS format"""
    if seconds <= 0:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def get_affix_emoji(affix_name):
    """Get emoji for affix"""
    affix_emojis = {
        "Tyrannical": "👑",
        "Fortified": "🛡️",
        "Bolstering": "💪",
        "Bursting": "💥",
        "Raging": "😡",
        "Sanguine": "🩸",
        "Volcanic": "🌋",
        "Explosive": "💣",
        "Quaking": "🌊",
        "Grievous": "⚔️",
        "Necrotic": "☠️",
        "Storming": "⛈️",
        "Afflicted": "🤢",
        "Incorporeal": "👻",
        "Entangling": "🌿",
        "Xal'atath's Bargain": "🔮"
    }
    return affix_emojis.get(affix_name, "🔸")

def analyze_recent_runs(server, character):
    """Get recent M+ runs with upgrade info"""
    print(f"📊 Analyzing {character}@{server}...")
    
    data = get_character_recent_mplus(server, character)
    
    if not data:
        return None
    
    # Get character info
    char_info = {
        "name": data.get("name", character),
        "class": data.get("class", "Unknown"),
        "spec": data.get("active_spec_name", "Unknown"),
        "ilvl": data.get("gear", {}).get("item_level_equipped", 0),
        "faction": data.get("faction", "Unknown"),
        "thumbnail": data.get("thumbnail_url", "")
    }
    
    # Get M+ score
    scores_by_season = data.get("mythic_plus_scores_by_season", [])
    score = 0
    if scores_by_season:
        score = scores_by_season[0].get("scores", {}).get("all", 0)
    
    char_info["score"] = score
    
    # Get recent runs
    recent_runs = data.get("mythic_plus_recent_runs", [])
    
    # Sort by completion time (most recent first)
    recent_runs.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    
    # Get top 10 recent runs
    best_runs = []
    for run in recent_runs[:10]:
        # Calculate upgrade level
        num_upgrades = run.get("num_keystone_upgrades", 0)
        upgrade_text = ""
        if num_upgrades > 0:
            upgrade_text = f"+{num_upgrades}"
        
        run_data = {
            "dungeon": run.get("dungeon", "Unknown"),
            "short_name": run.get("short_name", "Unknown"),
            "level": run.get("mythic_level", 0),
            "score": run.get("score", 0),
            "num_chests": run.get("num_keystone_upgrades", 0),
            "upgrade_text": upgrade_text,
            "timed": run.get("num_keystone_upgrades", 0) > 0,
            "clear_time_ms": run.get("clear_time_ms", 0),
            "par_time_ms": run.get("par_time_ms", 0),
            "completed_at": run.get("completed_at", ""),
            "url": run.get("url", ""),
            "affixes": [
                {
                    "name": affix.get("name", "Unknown"),
                    "description": affix.get("description", "")
                }
                for affix in run.get("affixes", [])
            ],
            "roster": []
        }
        
        # Get party roster
        roster = run.get("roster", [])
        for member in roster:
            character_info = member.get("character", {})
            member_data = {
                "name": character_info.get("name", "Unknown"),
                "class": character_info.get("class", {}).get("name", "Unknown") if isinstance(character_info.get("class"), dict) else character_info.get("class", "Unknown"),
                "spec": character_info.get("spec", {}).get("name", "Unknown") if isinstance(character_info.get("spec"), dict) else character_info.get("spec", "Unknown"),
                "role": member.get("role", "DPS")
            }
            run_data["roster"].append(member_data)
        
        best_runs.append(run_data)
    
    print(f"  ✅ Found {len(best_runs)} recent runs (score: {score:.1f})")
    
    return {
        "character": char_info,
        "best_runs": best_runs  # Keep same key name for compatibility
    }

def save_recent_mplus_data(csv_file="characters.csv"):
    """Fetch and save recent M+ data"""
    import csv
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return None
    
    characters_mplus = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        characters = list(reader)
    
    print(f"\n🏔️ Fetching recent M+ runs for {len(characters)} characters...")
    print("="*60 + "\n")
    
    for i, row in enumerate(characters, 1):
        server = row['Server'].strip()
        character = row['ID'].strip()
        
        print(f"[{i}/{len(characters)}] {character}@{server}")
        char_data = analyze_recent_runs(server, character)
        
        if char_data:
            characters_mplus[character] = char_data
        else:
            print(f"  ⚠️ No data available")
        
        # Rate limit protection
        time.sleep(0.3)
        print()
    
    # Save to JSON
    os.makedirs("logs", exist_ok=True)
    with open("logs/mplus_enhanced.json", 'w', encoding='utf-8') as f:
        json.dump(characters_mplus, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Recent M+ data saved to logs/mplus_enhanced.json")
    print("="*60)
    
    return characters_mplus

if __name__ == "__main__":
    print("🏔️ Recent M+ Runs Fetcher\n")
    save_recent_mplus_data()
