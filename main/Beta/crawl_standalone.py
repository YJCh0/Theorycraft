"""
Standalone Enhanced Crawler - No dependencies on original crawl.py
Save as: crawl_standalone.py
"""
import csv
import os
import time
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv

# Import enhanced WCL module
from wcl_enhanced import (
    WarcraftLogsAPI, 
    analyze_performance_consistency,
    calculate_raid_readiness,
    format_recent_activity
)

load_dotenv()

# Configuration
BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")
WCL_ACCESS_TOKEN = os.getenv("WCL_ACCESS_TOKEN")
BLIZZARD_TOKEN_URL = "https://kr.battle.net/oauth/token"
REGION = os.getenv("REGION", "kr")
NAMESPACE = os.getenv("NAMESPACE", "profile-kr")

# ══════════════════════════════════════════════════════
# TOKEN MANAGER
# ══════════════════════════════════════════════════════

class TokenManager:
    def __init__(self):
        self.token = None
        self.expiry = 0
    
    def get_token(self):
        """Get valid Blizzard API token with automatic refresh"""
        if not self.token or time.time() > self.expiry:
            print("🔄 Refreshing Blizzard token...")
            self.token = self._fetch_token()
            self.expiry = time.time() + (60 * 50)  # 50 minutes
        return self.token
    
    def _fetch_token(self):
        """Fetch new token from Blizzard OAuth"""
        data = {"grant_type": "client_credentials"}
        try:
            r = requests.post(
                BLIZZARD_TOKEN_URL,
                data=data,
                auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
                timeout=10
            )
            r.raise_for_status()
            token = r.json().get("access_token")
            print("✅ Blizzard token obtained")
            return token
        except requests.exceptions.RequestException as e:
            print(f"❌ Token fetch failed: {e}")
            return None

token_manager = TokenManager()

# ══════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════

def safe_request(method, url, retries=3, backoff=2, **kwargs):
    """Robust API request with retry logic"""
    for attempt in range(1, retries + 1):
        try:
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 15
            
            resp = requests.request(method, url, **kwargs)
            
            if resp.status_code == 404:
                return None
            
            if resp.status_code == 403:
                print("🔄 Token expired - refreshing...")
                if "headers" in kwargs and "Authorization" in kwargs["headers"]:
                    kwargs["headers"]["Authorization"] = f"Bearer {token_manager.get_token()}"
                continue
            
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", backoff ** attempt))
                print(f"⏳ Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            
            resp.raise_for_status()
            time.sleep(0.1)  # Rate limit protection
            return resp
            
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(backoff ** attempt)
        except requests.exceptions.RequestException as e:
            if attempt >= retries:
                print(f"⚠ Request failed: {e}")
                return None
            time.sleep(backoff ** attempt)
    
    return None

def format_amount(value):
    """Format float with 1 decimal"""
    if value is None or value == "N/A":
        return "N/A"
    try:
        return f"{float(value):,.1f}"
    except:
        return str(value)

def format_int(value):
    """Format integer with thousands separator"""
    if value is None or value == "N/A" or value == 0:
        return "N/A"
    try:
        return f"{int(round(float(value))):,}"
    except:
        return str(value)

def process_character_name(name):
    """영어 이름은 소문자, 한글은 그대로"""
    if any(ord(c) > 128 for c in name):  # Korean characters
        return name
    return name.lower()

# ══════════════════════════════════════════════════════
# TWW SEASON 3 UPGRADE TRACKS
# ══════════════════════════════════════════════════════

UPGRADE_TRACKS = {
    'myth': {
        'base': 707,
        'max_upgrades': 8,
        'levels': [707, 710, 714, 717, 720, 723, 727, 730]
    },
    'hero': {
        'base': 694,
        'max_upgrades': 8,
        'levels': [694, 697, 701, 704, 707, 710, 714, 717]
    },
    'champion': {
        'base': 681,
        'max_upgrades': 8,
        'levels': [681, 684, 688, 691, 694, 697, 701, 704]
    },
    'veteran': {
        'base': 668,
        'max_upgrades': 8,
        'levels': [668, 671, 675, 678, 681, 684, 688, 691]
    },
    'adventurer': {
        'base': 655,
        'max_upgrades': 8,
        'levels': [655, 658, 661, 665, 668, 671, 675, 678]
    },
    'explorer': {
        'base': 643,
        'max_upgrades': 8,
        'levels': [643, 646, 649, 652, 655, 658, 661, 665]
    }
}

def detect_upgrade_track(item_level):
    """Detect upgrade track and level from item level"""
    for track_name, track_info in UPGRADE_TRACKS.items():
        if item_level in track_info['levels']:
            upgrade_level = track_info['levels'].index(item_level)
            return (track_name.title(), upgrade_level, track_info['max_upgrades'])
    
    # Beyond max myth track
    if item_level >= 730:
        return ("Myth", 8, 8)
    
    return None

def format_upgrade_info(item_level):
    """Format upgrade info string"""
    upgrade_info = detect_upgrade_track(item_level)
    if upgrade_info:
        track, current, maximum = upgrade_info
        return f"{track} {current+1}/{maximum}"
    return "Max/Unknown"

# ══════════════════════════════════════════════════════
# BLIZZARD API FUNCTIONS
# ══════════════════════════════════════════════════════

def get_spec_icon(spec_id, token):
    """Get specialization icon URL"""
    if not spec_id or not token:
        return ""
    
    url = f"https://{REGION}.api.blizzard.com/data/wow/media/playable-specialization/{spec_id}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": "static-kr", "locale": "ko_KR"}
    
    resp = safe_request("GET", url, headers=headers, params=params)
    if not resp:
        return ""
    
    try:
        data = resp.json()
        assets = data.get("assets", [])
        for asset in assets:
            if asset.get("key") == "icon":
                return asset.get("value", "")
    except:
        pass
    
    return ""

def get_character_spec(server, character):
    """Get character's active specialization with icon"""
    token = token_manager.get_token()
    if not token:
        return "Unknown", ""
    
    character_processed = process_character_name(character)
    url = f"https://{REGION}.api.blizzard.com/profile/wow/character/{server.lower()}/{quote(character_processed)}/specializations"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": NAMESPACE, "locale": "ko_KR"}
    
    resp = safe_request("GET", url, headers=headers, params=params)
    if not resp:
        return "Unknown", ""
    
    try:
        data = resp.json()
        specializations = data.get("specializations", [])
        
        # Find active spec
        for spec_group in specializations:
            if spec_group.get("is_active", False):
                spec_info = spec_group.get("specialization", {})
                spec_name = spec_info.get("name", "Unknown")
                spec_id = spec_info.get("id", 0)
                spec_icon = get_spec_icon(spec_id, token)
                return spec_name, spec_icon
        
        # Fallback to first spec
        if specializations:
            spec_info = specializations[0].get("specialization", {})
            spec_name = spec_info.get("name", "Unknown")
            spec_id = spec_info.get("id", 0)
            spec_icon = get_spec_icon(spec_id, token)
            return spec_name, spec_icon
        
        return "Unknown", ""
    except Exception as e:
        print(f"⚠ Failed to parse spec: {e}")
        return "Unknown", ""

def get_item_icon(item_id, token):
    """Get item icon URL"""
    if not item_id or not token:
        return ""
    
    url = f"https://{REGION}.api.blizzard.com/data/wow/media/item/{item_id}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": "static-kr", "locale": "ko_KR"}
    
    resp = safe_request("GET", url, headers=headers, params=params)
    if not resp:
        return ""
    
    try:
        data = resp.json()
        assets = data.get("assets", [])
        for asset in assets:
            if asset.get("key") == "icon":
                return asset.get("value", "")
    except:
        pass
    
    return ""

def get_character_equipment(server, character):
    """Get character equipment with upgrade tracking"""
    token = token_manager.get_token()
    if not token:
        return []
    
    character_processed = process_character_name(character)
    url = f"https://{REGION}.api.blizzard.com/profile/wow/character/{server.lower()}/{quote(character_processed)}/equipment"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": NAMESPACE, "locale": "ko_KR"}
    
    resp = safe_request("GET", url, headers=headers, params=params)
    if not resp:
        return []
    
    try:
        data = resp.json()
        equipped = data.get("equipped_items", [])
        
        equipment_list = []
        for item in equipped:
            slot_name = item.get("slot", {}).get("name", "Unknown")
            item_name = item.get("name", "Unknown")
            item_level = item.get("level", {}).get("value", 0)
            item_id = item.get("item", {}).get("id", 0)
            
            icon_url = get_item_icon(item_id, token)
            upgrade_text = format_upgrade_info(item_level)
            
            equipment_list.append({
                "slot": slot_name,
                "name": item_name,
                "ilvl": item_level,
                "item_id": item_id,
                "icon": icon_url,
                "upgrade": upgrade_text
            })
        
        return equipment_list
    except Exception as e:
        print(f"⚠ Failed to parse equipment: {e}")
        return []

def get_ilvl_from_blizzard(server, character):
    """Get character average item level"""
    token = token_manager.get_token()
    if not token:
        return 0
    
    character_processed = process_character_name(character)
    url = f"https://{REGION}.api.blizzard.com/profile/wow/character/{server.lower()}/{quote(character_processed)}/equipment"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": NAMESPACE, "locale": "ko_KR"}
    
    resp = safe_request("GET", url, headers=headers, params=params)
    if not resp:
        return 0
    
    try:
        data = resp.json()
        equipped = data.get("equipped_items", [])
        if not equipped:
            return 0
        
        # Filter out cosmetic slots
        ilvls = []
        for item in equipped:
            slot_name = item.get("slot", {}).get("name", "")
            if slot_name not in ["속옷", "겉옷"]:  # Exclude shirt/tabard
                ilvls.append(item["level"]["value"])
        
        return round(sum(ilvls) / len(ilvls), 1) if ilvls else 0
    except Exception as e:
        print(f"⚠ Failed to parse ilvl: {e}")
        return 0

# ══════════════════════════════════════════════════════
# RAIDER.IO API
# ══════════════════════════════════════════════════════

def get_mplus_score(server, character):
    """Get M+ score from Raider.IO"""
    url = "https://raider.io/api/v1/characters/profile"
    params = {
        "region": REGION,
        "realm": server,
        "name": character,
        "fields": "mythic_plus_scores_by_season:current"
    }
    
    resp = safe_request("GET", url, params=params)
    if not resp:
        return "N/A"
    
    try:
        data = resp.json()
        seasons = data.get("mythic_plus_scores_by_season", [])
        
        # Try current season
        for season in seasons:
            if "season-tww-3" in season.get("season", ""):
                return season.get("scores", {}).get("all", "N/A")
        
        # Fallback to most recent
        if seasons:
            return seasons[0].get("scores", {}).get("all", "N/A")
        
        return "N/A"
    except:
        return "N/A"

# ══════════════════════════════════════════════════════
# MAIN CRAWLER
# ══════════════════════════════════════════════════════

# Initialize WCL API
wcl_api = WarcraftLogsAPI(WCL_ACCESS_TOKEN)

def crawl_character_standalone(row, attempt=1):
    """Standalone character crawl - no dependencies"""
    server = row["Server"].strip()
    character = row["ID"].strip()
    role = row["Role"].strip()
    character_class = row["Class"].strip()
    
    print(f"[{attempt}] 🔍 {character}@{server}")
    
    try:
        # Get Blizzard data
        equipment_data = get_character_equipment(server, character)
        ilvl = get_ilvl_from_blizzard(server, character)
        mplus_score = get_mplus_score(server, character)
        blizzard_spec, blizzard_spec_icon = get_character_spec(server, character)
        
        # Get enhanced WCL data
        print(f"  📊 Fetching WCL data...")
        wcl_data = wcl_api.get_comprehensive_character_data(
            name=character,
            server=server,
            region=REGION,
            role=role
        )
        
        # Retry logic
        if (not wcl_data or ilvl == 0) and attempt < 3:
            print(f"  ⚠️ Retrying...")
            time.sleep(2)
            return crawl_character_standalone(row, attempt + 1)
        
        # Process WCL data
        mythic_data = wcl_data.get('mythic', {})
        heroic_data = wcl_data.get('heroic', {})
        recent_activity = wcl_data.get('recent_activity', [])
        
        # Get best performance
        best_perf_avg = mythic_data.get('best_performance', "N/A")
        if best_perf_avg == "N/A" or best_perf_avg is None:
            best_perf_avg = heroic_data.get('best_performance', "N/A")
        
        # Calculate metrics
        mythic_boss_rankings = mythic_data.get('boss_rankings', [])
        consistency_analysis = analyze_performance_consistency(mythic_boss_rankings)
        
        # Raid readiness
        try:
            mplus_val = float(str(mplus_score).replace(',', '')) if mplus_score != "N/A" else 0
            wcl_val = float(str(best_perf_avg).replace(',', '')) if best_perf_avg != "N/A" else 0
            readiness = calculate_raid_readiness(ilvl, mplus_val, wcl_val)
        except:
            readiness = {'score': 0, 'rating': 'Unknown', 'components': {}}
        
        # Get spec
        all_stars = mythic_data.get('all_stars', [])
        if not all_stars:
            all_stars = heroic_data.get('all_stars', [])
        wcl_spec = all_stars[0].get('spec', blizzard_spec) if all_stars else blizzard_spec
        
        # Save report
        os.makedirs("detailed", exist_ok=True)
        report = format_comprehensive_report(
            character, character_class, role, server, wcl_spec, blizzard_spec_icon,
            equipment_data, ilvl, mplus_score, wcl_data, consistency_analysis, readiness
        )
        
        with open(f"detailed/{character}.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"  ✅ Complete! Consistency: {consistency_analysis['consistency_rating']}")
        
        return {
            'csv_row': [
                character,
                character_class,
                wcl_spec,
                ilvl,
                format_amount(mplus_score),
                format_amount(best_perf_avg) if best_perf_avg != "N/A" else "N/A"
            ],
            'enhanced_data': {
                'name': character,
                'server': server,
                'class': character_class,
                'spec': wcl_spec,
                'role': role,
                'ilvl': ilvl,
                'mplus_score': mplus_score,
                'wcl_mythic': mythic_data,
                'wcl_heroic': heroic_data,
                'recent_activity': recent_activity,
                'consistency': consistency_analysis,
                'readiness': readiness
            }
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            'csv_row': [character, character_class, "N/A", 0, "N/A", "N/A"],
            'enhanced_data': None
        }

def format_comprehensive_report(character, character_class, role, server, spec, 
                                spec_icon, equipment_data, ilvl, mplus_score, 
                                wcl_data, consistency_analysis, readiness):
    """Format enhanced character report"""
    lines = []
    
    # Header
    lines.append(f"# {character}")
    lines.append(f"**{spec} {character_class}** | **{role}** | **{server}**")
    lines.append(f"**SPEC_ICON:{spec_icon}**")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    lines.append("---\n")
    
    mythic_data = wcl_data.get('mythic', {})
    heroic_data = wcl_data.get('heroic', {})
    recent_activity = wcl_data.get('recent_activity', [])
    
    # Overview
    lines.append("## 📊 Overview\n")
    lines.append(f"- **Item Level:** {ilvl}")
    lines.append(f"- **M+ Score:** {format_amount(mplus_score)}")
    lines.append(f"- **WCL Mythic:** {format_amount(mythic_data.get('best_performance'))}")
    lines.append(f"- **WCL Heroic:** {format_amount(heroic_data.get('best_performance'))}\n")
    
    # Raid Readiness
    lines.append("### 🎯 Raid Readiness\n")
    lines.append(f"- **Score:** {readiness['score']:.1f}/100")
    lines.append(f"- **Rating:** {readiness['rating']}\n")
    
    # Consistency
    if consistency_analysis['total_bosses'] > 0:
        lines.append("### 📈 Consistency\n")
        lines.append(f"- **Rating:** {consistency_analysis['consistency_rating']}")
        lines.append(f"- **Score:** {consistency_analysis['average_consistency']:.1f}%\n")
    
    # Equipment
    lines.append("---\n## ⚔️ Equipment\n")
    if equipment_data:
        lines.append("| Slot | Item | ilvl | Upgrade | Icon |")
        lines.append("|------|------|------|---------|------|")
        for item in equipment_data:
            lines.append(f"| {item['slot']} | {item['name']} | {item['ilvl']} | {item['upgrade']} | ICON:{item['icon']} |")
    
    # Recent Activity
    if recent_activity:
        lines.append("\n---\n## 📅 Recent Activity\n")
        lines.append("| Date | Duration | Kills | Wipes |")
        lines.append("|------|----------|-------|-------|")
        for raid in recent_activity[:5]:
            lines.append(f"| {raid['date']} | {raid['duration_minutes']:.0f}m | {raid['kills']} | {raid['wipes']} |")
    
    # Mythic
    lines.append("\n---\n## 🏆 Mythic Performance\n")
    if mythic_data and mythic_data.get('boss_rankings'):
        lines.append("| Boss | Best % | Consistency | DPS/HPS | Kills |")
        lines.append("|------|--------|-------------|---------|-------|")
        for boss in mythic_data['boss_rankings']:
            lines.append(f"| {boss['boss']} | {boss['rank_percent']:.1f}% | {boss['consistency_score']:.0f}% | {format_int(boss['best_amount'])} | {boss['total_kills']} |")
    else:
        lines.append("*No mythic logs*")
    
    # Heroic
    lines.append("\n---\n## 🏆 Heroic Performance\n")
    if heroic_data and heroic_data.get('boss_rankings'):
        lines.append("| Boss | Best % | DPS/HPS | Kills |")
        lines.append("|------|--------|---------|-------|")
        for boss in heroic_data['boss_rankings']:
            lines.append(f"| {boss['boss']} | {boss['rank_percent']:.1f}% | {format_int(boss['best_amount'])} | {boss['total_kills']} |")
    else:
        lines.append("*No heroic logs*")
    
    lines.append("\n---")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def main():
    """Main execution"""
    start_time = time.time()
    
    os.makedirs("logs", exist_ok=True)
    os.makedirs("detailed", exist_ok=True)
    
    if not os.path.exists("characters.csv"):
        print("❌ characters.csv not found")
        return
    
    with open("characters.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        characters = list(reader)
    
    print(f"\n🎮 Standalone Enhanced Crawler")
    print(f"📊 Processing {len(characters)} characters\n")
    
    results = []
    enhanced_data_all = []
    
    # Process with thread pool
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(crawl_character_standalone, char) for char in characters]
        
        for future in futures:
            result = future.result()
            if result:
                results.append(result['csv_row'])
                if result['enhanced_data']:
                    enhanced_data_all.append(result['enhanced_data'])
    
    # Save CSV
    with open("logs/Player_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Class", "Spec", "ilvl", "M+", "WCL"])
        writer.writerows(results)
    
    # Save JSON
    import json
    with open("logs/characters_enhanced.json", "w", encoding="utf-8") as f:
        json.dump(enhanced_data_all, f, indent=2, ensure_ascii=False)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Complete in {elapsed:.1f}s")
    print(f"📁 Results: logs/Player_data.csv")
    print(f"📊 Enhanced: logs/characters_enhanced.json")

if __name__ == "__main__":
    main()
