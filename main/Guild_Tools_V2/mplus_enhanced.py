import requests
import json
import os
import time
from datetime import datetime

REGION = os.getenv("REGION", "kr")

def get_character_detailed_mplus(server, character):
    """Get comprehensive M+ data including runs, roster, affixes"""
    url = "https://raider.io/api/v1/characters/profile"
    params = {
        "region": REGION,
        "realm": server,
        "name": character,
        "fields": "mythic_plus_scores_by_season:current,mythic_plus_recent_runs,mythic_plus_highest_level_runs,mythic_plus_weekly_highest_level_runs,gear"
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

def analyze_best_runs(server, character):
    """Get detailed analysis of character's best M+ runs"""
    print(f"📊 Analyzing {character}@{server}...")
    
    data = get_character_detailed_mplus(server, character)
    
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
    
    # Get highest level runs (these are typically the best runs)
    highest_runs = data.get("mythic_plus_highest_level_runs", [])
    recent_runs = data.get("mythic_plus_recent_runs", [])
    
    all_runs = highest_runs + recent_runs
    
    # Remove duplicates based on dungeon + key level
    seen = set()
    unique_runs = []
    for run in all_runs:
        key = (run.get("dungeon"), run.get("mythic_level"))
        if key not in seen:
            seen.add(key)
            unique_runs.append(run)
    
    # Sort by key level, then by score
    unique_runs.sort(key=lambda x: (x.get("mythic_level", 0), x.get("score", 0)), reverse=True)
    
    # Get top 5 runs
    best_runs = []
    for run in unique_runs[:5]:
        run_data = {
            "dungeon": run.get("dungeon", "Unknown"),
            "short_name": run.get("short_name", "Unknown"),
            "level": run.get("mythic_level", 0),
            "score": run.get("score", 0),
            "num_chests": run.get("num_chests", 0),
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
    
    print(f"  ✅ Found {len(best_runs)} best runs (score: {score:.1f})")
    
    return {
        "character": char_info,
        "best_runs": best_runs
    }

def generate_enhanced_mplus_html(characters_data):
    """Generate enhanced HTML with detailed run information"""
    
    html = """
    <style>
        .mplus-enhanced {
            padding: 20px;
        }
        .character-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .char-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }
        .char-avatar {
            width: 80px;
            height: 80px;
            border-radius: 10px;
            margin-right: 20px;
            border: 3px solid #667eea;
        }
        .char-info h3 {
            margin: 0;
            color: #667eea;
            font-size: 1.8em;
        }
        .char-stats {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }
        .stat-badge {
            background: #f0f0f0;
            padding: 5px 15px;
            border-radius: 8px;
            font-size: 0.9em;
        }
        .run-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        .run-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .dungeon-name {
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
        }
        .key-level {
            font-size: 1.5em;
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 8px;
            color: white;
        }
        .affixes {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .affix {
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.85em;
        }
        .roster {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        .roster-member {
            background: white;
            padding: 10px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .role-icon {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
        }
        .tank { background: #C41E3A; }
        .healer { background: #1EFF00; }
        .dps { background: #667eea; }
        .time-info {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }
        .raiderio-link {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .raiderio-link:hover {
            background: #764ba2;
        }
    </style>
    
    <div class="mplus-enhanced">
        <h2 style="color: #667eea; margin-bottom: 30px;">🏔️ Mythic+ Best Runs - Detailed View</h2>
    """
    
    if not characters_data:
        html += "<p>No M+ data available</p></div>"
        return html
    
    # Sort by score
    sorted_chars = sorted(
        [(name, data) for name, data in characters_data.items() if data],
        key=lambda x: x[1]["character"]["score"],
        reverse=True
    )
    
    for char_name, char_data in sorted_chars:
        char_info = char_data["character"]
        best_runs = char_data["best_runs"]
        
        if not best_runs:
            continue
        
        # Character header
        html += f"""
        <div class="character-section">
            <div class="char-header">
                <img src="{char_info['thumbnail']}" alt="{char_info['name']}" class="char-avatar" onerror="this.style.display='none'">
                <div class="char-info">
                    <h3>{char_info['name']}</h3>
                    <div class="char-stats">
                        <span class="stat-badge">{char_info['spec']} {char_info['class']}</span>
                        <span class="stat-badge">ilvl {char_info['ilvl']}</span>
                        <span class="stat-badge" style="background: #667eea; color: white;">M+ Score: {char_info['score']:.0f}</span>
                    </div>
                </div>
            </div>
        """
        
        # Best runs
        for i, run in enumerate(best_runs, 1):
            # Color code by level
            if run['level'] >= 12:
                level_color = "#FF8000"  # Orange
            elif run['level'] >= 10:
                level_color = "#A335EE"  # Purple
            elif run['level'] >= 8:
                level_color = "#0070DD"  # Blue
            else:
                level_color = "#1EFF00"  # Green
            
            timed_icon = "✅ Timed" if run['timed'] else "❌ Depleted"
            upgrade_text = f"+{run['num_chests']}" if run['timed'] else ""
            
            clear_time = format_duration(run['clear_time_ms'] / 1000)
            par_time = format_duration(run['par_time_ms'] / 1000)
            time_diff = (run['clear_time_ms'] - run['par_time_ms']) / 1000
            time_diff_str = f"+{format_duration(abs(time_diff))}" if time_diff > 0 else f"-{format_duration(abs(time_diff))}"
            
            # Format completion time
            if run['completed_at']:
                try:
                    completed = datetime.fromisoformat(run['completed_at'].replace('Z', '+00:00'))
                    completed_str = completed.strftime('%Y-%m-%d %H:%M')
                except:
                    completed_str = run['completed_at']
            else:
                completed_str = "Unknown"
            
            html += f"""
            <div class="run-card">
                <div class="run-header">
                    <div>
                        <div class="dungeon-name">#{i} {run['dungeon']}</div>
                        <div style="color: #666; font-size: 0.9em; margin-top: 5px;">{completed_str}</div>
                    </div>
                    <div class="key-level" style="background: {level_color};">
                        +{run['level']} {upgrade_text}
                    </div>
                </div>
                
                <div style="margin-bottom: 10px; font-weight: 600; color: {'#28a745' if run['timed'] else '#dc3545'};">
                    {timed_icon} | Score: {run['score']:.1f}
                </div>
                
                <div class="affixes">
            """
            
            for affix in run['affixes']:
                emoji = get_affix_emoji(affix['name'])
                html += f'<span class="affix" title="{affix.get("description", "")}">{emoji} {affix["name"]}</span>'
            
            html += f"""
                </div>
                
                <div class="time-info">
                    <span>⏱️ Clear Time: <strong>{clear_time}</strong></span>
                    <span>🎯 Par Time: <strong>{par_time}</strong></span>
                    <span>📊 Difference: <strong style="color: {'#28a745' if time_diff <= 0 else '#dc3545'};">{time_diff_str}</strong></span>
                </div>
                
                <h4 style="margin-top: 15px; margin-bottom: 10px; color: #667eea;">Party Composition</h4>
                <div class="roster">
            """
            
            for member in run['roster']:
                role_class = member['role'].lower()
                role_emoji = "🛡️" if role_class == "tank" else "💚" if role_class == "healer" else "⚔️"
                
                html += f"""
                    <div class="roster-member">
                        <div class="role-icon {role_class}">{role_emoji}</div>
                        <div>
                            <div style="font-weight: 600;">{member['name']}</div>
                            <div style="font-size: 0.85em; color: #666;">{member['spec']} {member['class']}</div>
                        </div>
                    </div>
                """
            
            html += "</div>"
            
            if run['url']:
                html += f'<a href="{run["url"]}" target="_blank" class="raiderio-link">📊 View on Raider.IO</a>'
            
            html += "</div>"
        
        html += "</div>"
    
    html += "</div>"
    
    return html

def save_enhanced_mplus_data(csv_file="characters.csv"):
    """Fetch and save enhanced M+ data"""
    import csv
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return None
    
    characters_mplus = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        characters = list(reader)
    
    print(f"\n🏔️ Fetching enhanced M+ data for {len(characters)} characters...")
    print("="*60 + "\n")
    
    for i, row in enumerate(characters, 1):
        server = row['Server'].strip()
        character = row['ID'].strip()
        
        print(f"[{i}/{len(characters)}] {character}@{server}")
        char_data = analyze_best_runs(server, character)
        
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
    
    print(f"\n✅ Enhanced M+ data saved to logs/mplus_enhanced.json")
    
    # Generate preview HTML
    html = generate_enhanced_mplus_html(characters_mplus)
    
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced M+ Runs</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        {html}
    </div>
</body>
</html>
    """
    
    with open("logs/mplus_enhanced.html", 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"📄 Preview saved to logs/mplus_enhanced.html")
    print("="*60)
    
    return characters_mplus

if __name__ == "__main__":
    print("🏔️ Enhanced M+ Analysis with Run Details\n")
    save_enhanced_mplus_data()
