import csv
import os
import time
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.theme import Theme
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Settings
INPUT_FILE = "characters.csv"
OUTPUT_DIR = "logs"
DETAIL_DIR = "detailed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Player_data.csv")
FAILED_LOG = os.path.join(OUTPUT_DIR, "failed_characters.log")
PREVIOUS_FILE = os.path.join(OUTPUT_DIR, "previous_Player_data.csv")
WEEKLY_FILE = os.path.join(OUTPUT_DIR, "weekly_comparison.csv")

# API Credentials
BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")
WCL_ACCESS_TOKEN = os.getenv("WCL_ACCESS_TOKEN")

if not all([BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET, WCL_ACCESS_TOKEN]):
    raise ValueError("❌ Missing API credentials! Please check your .env file.")

BLIZZARD_TOKEN_URL = "https://kr.battle.net/oauth/token"
REGION = os.getenv("REGION", "kr")
NAMESPACE = os.getenv("NAMESPACE", "profile-kr")

theme = Theme({"info": "cyan", "success": "bold green", "error": "bold red", "warning": "yellow"})
console = Console(theme=theme)

# TWW Season 3 Upgrade Tracks
UPGRADE_TRACKS = {
    'myth': {'base': 707, 'max_upgrades': 8, 'upgrade_increment': 3, 'levels': [707, 710, 714, 717, 720, 723, 727, 730]},
    'hero': {'base': 694, 'max_upgrades': 8, 'upgrade_increment': 3, 'levels': [694, 697, 701, 704, 707, 710, 714, 717]},
    'champion': {'base': 681, 'max_upgrades': 8, 'upgrade_increment': 3, 'levels': [681, 684, 688, 691, 694, 697, 701, 704]},
    'veteran': {'base': 668, 'max_upgrades': 8, 'upgrade_increment': 3, 'levels': [668, 671, 675, 678, 681, 684, 688, 691]},
    'adventurer': {'base': 655, 'max_upgrades': 8, 'upgrade_increment': 3, 'levels': [655, 658, 661, 665, 668, 671, 675, 678]},
    'explorer': {'base': 643, 'max_upgrades': 8, 'upgrade_increment': 3, 'levels': [643, 646, 649, 652, 655, 658, 661, 665]}
}

def detect_upgrade_track(item_level):
    """Detect which upgrade track and upgrade level based on item level"""
    for track_name, track_info in UPGRADE_TRACKS.items():
        if item_level in track_info['levels']:
            upgrade_level = track_info['levels'].index(item_level)
            return (track_name.title(), upgrade_level, track_info['max_upgrades'])
    
    myth_max = UPGRADE_TRACKS['myth']['base'] + (UPGRADE_TRACKS['myth']['max_upgrades'] * UPGRADE_TRACKS['myth']['upgrade_increment'])
    if item_level >= myth_max:
        return ("Myth", 8, 8)
    
    return None

def format_upgrade_info(item_level):
    """Format upgrade info as readable string"""
    upgrade_info = detect_upgrade_track(item_level)
    if upgrade_info:
        track, current, maximum = upgrade_info
        return f"{track} {current+1}/{maximum}"
    return "Max/Unknown"

# Token Management
class TokenManager:
    def __init__(self):
        self.token = None
        self.expiry = 0
    
    def get_token(self):
        """Get valid Blizzard API token with automatic refresh"""
        if not self.token or time.time() > self.expiry:
            console.print("[warning]🔄 Refreshing Blizzard token...[/warning]")
            self.token = self._fetch_token()
            self.expiry = time.time() + (60 * 50)
        return self.token
    
    def _fetch_token(self):
        """Fetch new token from Blizzard OAuth"""
        data = {"grant_type": "client_credentials"}
        try:
            r = requests.post(BLIZZARD_TOKEN_URL, data=data, auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET), timeout=10)
            r.raise_for_status()
            token = r.json().get("access_token")
            console.print("[success]✅ Blizzard token obtained[/success]")
            return token
        except requests.exceptions.RequestException as e:
            console.print(f"[error]❌ Token fetch failed: {e}[/error]")
            return None

token_manager = TokenManager()

# Utility Functions
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
                console.print("[warning]🔄 Token expired - refreshing...[/warning]")
                if "headers" in kwargs and "Authorization" in kwargs["headers"]:
                    kwargs["headers"]["Authorization"] = f"Bearer {token_manager.get_token()}"
                continue
            
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", backoff ** attempt))
                console.print(f"[warning]⏳ Rate limited. Waiting {retry_after}s...[/warning]")
                time.sleep(retry_after)
                continue
            
            resp.raise_for_status()
            time.sleep(0.1)
            return resp
            
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(backoff ** attempt)
        except requests.exceptions.RequestException as e:
            if attempt >= retries:
                console.print(f"[warning]⚠ Request failed: {e}[/warning]")
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
    if any(ord(c) > 128 for c in name):
        return name
    return name.lower()

# API Functions
def get_spec_icon(spec_id, token):
    """Get specialization icon URL from Blizzard media API"""
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
        
        for spec_group in specializations:
            if spec_group.get("is_active", False):
                spec_info = spec_group.get("specialization", {})
                spec_name = spec_info.get("name", "Unknown")
                spec_id = spec_info.get("id", 0)
                spec_icon = get_spec_icon(spec_id, token)
                return spec_name, spec_icon
        
        if specializations and len(specializations) > 0:
            spec_info = specializations[0].get("specialization", {})
            spec_name = spec_info.get("name", "Unknown")
            spec_id = spec_info.get("id", 0)
            spec_icon = get_spec_icon(spec_id, token)
            return spec_name, spec_icon
        
        return "Unknown", ""
    except (KeyError, ValueError, TypeError) as e:
        console.print(f"[warning]⚠ Failed to parse spec: {e}[/warning]")
        return "Unknown", ""

def get_item_icon(item_id, token):
    """Get item icon URL from Blizzard media API"""
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
    """Get detailed equipment list with trinkets marked"""
    token = token_manager.get_token()
    if not token:
        return [], []
    
    character_processed = process_character_name(character)
    url = f"https://{REGION}.api.blizzard.com/profile/wow/character/{server.lower()}/{quote(character_processed)}/equipment"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": NAMESPACE, "locale": "ko_KR"}
    
    resp = safe_request("GET", url, headers=headers, params=params)
    if not resp:
        return [], []
    
    try:
        data = resp.json()
        equipped = data.get("equipped_items", [])
        
        equipment_list = []
        trinkets = []
        
        for item in equipped:
            slot_name = item.get("slot", {}).get("name", "Unknown")
            item_name = item.get("name", "Unknown")
            item_level = item.get("level", {}).get("value", 0)
            item_id = item.get("item", {}).get("id", 0)
            icon_url = get_item_icon(item_id, token)
            
            upgrade_info = detect_upgrade_track(item_level)
            if upgrade_info:
                track, current, maximum = upgrade_info
                upgrade_text = f"{track} {current+1}/{maximum}"
            else:
                if item_level >= 730:
                    upgrade_text = "Max"
                else:
                    upgrade_text = format_upgrade_info(item_level)
            
            item_data = {
                "slot": slot_name,
                "name": item_name,
                "ilvl": item_level,
                "item_id": item_id,
                "icon": icon_url,
                "upgrade": upgrade_text
            }
            
            equipment_list.append(item_data)
            
            # Track trinkets
            if "장신구" in slot_name or "Trinket" in slot_name:
                trinkets.append(item_data)
        
        return equipment_list, trinkets
    except (KeyError, ValueError, TypeError) as e:
        console.print(f"[warning]⚠ Failed to parse equipment: {e}[/warning]")
        return [], []

def get_ilvl_from_blizzard(server, character):
    """Get character average ilvl from Blizzard API"""
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
        
        ilvls = []
        for item in equipped:
            slot_name = item.get("slot", {}).get("name", "")
            if slot_name not in ["속옷", "겉옷"]:
                ilvls.append(item["level"]["value"])
        
        return round(sum(ilvls) / len(ilvls), 1) if ilvls else 0
    except (KeyError, ValueError, TypeError) as e:
        console.print(f"[warning]⚠ Failed to parse ilvl: {e}[/warning]")
        return 0

def get_mplus_score(server, character):
    """Get Mythic+ score from Raider.IO"""
    url = "https://raider.io/api/v1/characters/profile"
    params = {"region": REGION, "realm": server, "name": character, "fields": "mythic_plus_scores_by_season:current"}
    
    resp = safe_request("GET", url, params=params)
    if not resp:
        return "N/A"
    
    try:
        data = resp.json()
        seasons = data.get("mythic_plus_scores_by_season", [])
        
        for season in seasons:
            if "season-tww-3" in season.get("season", ""):
                return season.get("scores", {}).get("all", "N/A")
        
        if seasons:
            return seasons[0].get("scores", {}).get("all", "N/A")
        
        return "N/A"
    except (KeyError, ValueError, TypeError):
        return "N/A"

def get_wcl_data_with_trinkets(server, character, role):
    """Get WarcraftLogs data including trinket usage per boss"""
    metric = "hps" if role.lower() == "healer" else "dps"
    
    # Extended query to get encounter details with rankings
    query = """
    query($name: String!, $server: String!, $region: String!, $metric: CharacterRankingMetricType!) {
      characterData {
        character(name: $name, serverSlug: $server, serverRegion: $region) {
          name
          mythicRankings: zoneRankings(metric: $metric, difficulty: 5)
          heroicRankings: zoneRankings(metric: $metric, difficulty: 4)
        }
      }
    }
    """
    
    variables = {"name": character, "server": server.lower(), "region": REGION, "metric": metric}
    headers = {"Authorization": f"Bearer {WCL_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"query": query, "variables": variables}
    
    resp = safe_request("POST", "https://www.warcraftlogs.com/api/v2/client", headers=headers, json=payload)
    if not resp:
        return None
    
    try:
        data = resp.json()
        
        if 'errors' in data:
            error_msg = data['errors'][0].get('message', 'Unknown') if data['errors'] else 'Unknown'
            console.print(f"[warning]⚠ WCL error: {error_msg}[/warning]")
            return None
        
        character_info = data.get('data', {}).get('characterData', {}).get('character')
        
        if not character_info:
            console.print(f"[warning]⚠ {character}@{server} not found in WCL (no logs)[/warning]")
            return {}
        
        # Process rankings to include rank details
        mythic_rankings = character_info.get('mythicRankings', {})
        heroic_rankings = character_info.get('heroicRankings', {})
        
        # Add detailed rank info to each boss
        for rankings_data in [mythic_rankings, heroic_rankings]:
            if rankings_data and 'rankings' in rankings_data:
                for encounter in rankings_data['rankings']:
                    # Extract rank details if available
                    # Format: rank/totalParses (rankWorld)
                    rank = encounter.get('rank', 0)
                    total_parses = encounter.get('totalParses', 0)
                    region_rank = encounter.get('regionRank', 0)
                    
                    encounter['rankDetails'] = f"{rank}/{total_parses} (KR: {region_rank})" if rank and total_parses else ""
        
        return {
            'mythic': mythic_rankings,
            'heroic': heroic_rankings
        }
        
    except (KeyError, TypeError, ValueError) as e:
        console.print(f"[warning]⚠ WCL parse error: {e}[/warning]")
        return None

def format_comprehensive_report(character, character_class, role, server, wcl_spec, wcl_spec_icon,
                               equipment_data, trinkets, ilvl, mplus_score, wcl_data):
    """Format comprehensive character report with trinket data"""
    lines = []
    lines.append(f"# {character}")
    lines.append(f"**{wcl_spec} {character_class}** | **{role}** | **{server}**")
    lines.append(f"**SPEC_ICON:{wcl_spec_icon}**")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    lines.append("---\n")
    
    mythic_data = wcl_data.get('mythic', {}) if isinstance(wcl_data, dict) else wcl_data
    heroic_data = wcl_data.get('heroic', {}) if isinstance(wcl_data, dict) else {}
    
    # Overview
    lines.append("## 📊 Overview\n")
    lines.append(f"- **Average Item Level:** {ilvl}")
    lines.append(f"- **Mythic+ Score:** {format_amount(mplus_score)}")
    
    mythic_perf = mythic_data.get('bestPerformanceAverage') if mythic_data else None
    heroic_perf = heroic_data.get('bestPerformanceAverage') if heroic_data else None
    
    lines.append(f"- **WarcraftLogs Mythic Average:** {format_amount(mythic_perf)}")
    lines.append(f"- **WarcraftLogs Heroic Average:** {format_amount(heroic_perf)}\n")
    
    # Trinkets Section
    lines.append("---\n")
    lines.append("## 🎯 Current Trinkets\n")
    
    if trinkets:
        lines.append("| Trinket | Item Level | Upgrade | Icon |")
        lines.append("|---------|------------|---------|------|")
        
        for trinket in trinkets:
            name = trinket.get('name', 'Unknown')
            item_ilvl = trinket.get('ilvl', 0)
            upgrade = trinket.get('upgrade', 'Unknown')
            icon_url = trinket.get('icon', '')
            lines.append(f"| {name} | {item_ilvl} | {upgrade} | TRINKET_ICON:{icon_url} |")
    else:
        lines.append("*No trinket data available*")
    
    lines.append("")
    
    # Equipment
    lines.append("---\n")
    lines.append("## ⚔️ Equipment\n")
    
    if equipment_data:
        lines.append("| Slot | Item Name | Item Level | Upgrade | Icon |")
        lines.append("|------|-----------|------------|---------|------|")
        
        for item in equipment_data:
            slot = item.get('slot', 'Unknown')
            name = item.get('name', 'Unknown')
            item_ilvl = item.get('ilvl', 0)
            upgrade = item.get('upgrade', 'Unknown')
            icon_url = item.get('icon', '')
            lines.append(f"| {slot} | {name} | {item_ilvl} | {upgrade} | ICON:{icon_url} |")
    else:
        lines.append("*Equipment data not available*")
    
    lines.append("")
    
    # WarcraftLogs - Mythic
    lines.append("---\n")
    lines.append("## 🏆 WarcraftLogs Performance - Mythic\n")
    
    if not mythic_data or mythic_data == {}:
        lines.append("*No mythic raid logs found for this character*\n")
    else:
        mythic_perf = mythic_data.get('bestPerformanceAverage')
        if mythic_perf:
            lines.append(f"### Best Performance Average: **{format_amount(mythic_perf)}**\n")
        
        lines.append("### 📋 Boss Rankings\n")
        rankings = mythic_data.get('rankings', [])
        
        if rankings:
            lines.append("| Boss | Rank % | Best DPS/HPS | Total Kills | Rank Details |")
            lines.append("|------|--------|--------------|-------------|--------------|")
            
            for encounter in rankings:
                boss = encounter.get('encounter', {}).get('name', 'Unknown')
                rank_percent = encounter.get('rankPercent', 0)
                best_amount = encounter.get('bestAmount', 0)
                total_kills = encounter.get('totalKills', 0)
                rank_details = encounter.get('rankDetails', 'N/A')
                
                lines.append(f"| {boss} | {format_amount(rank_percent)}% | {format_int(best_amount)} | {total_kills} | {rank_details} |")
        else:
            lines.append("*No mythic boss rankings available*")
        
        lines.append("")
    
    # WarcraftLogs - Heroic
    lines.append("---\n")
    lines.append("## 🏆 WarcraftLogs Performance - Heroic\n")
    
    if not heroic_data or heroic_data == {}:
        lines.append("*No heroic raid logs found for this character*\n")
    else:
        heroic_perf = heroic_data.get('bestPerformanceAverage')
        if heroic_perf:
            lines.append(f"### Best Performance Average: **{format_amount(heroic_perf)}**\n")
        
        lines.append("### 📋 Boss Rankings\n")
        rankings = heroic_data.get('rankings', [])
        
        if rankings:
            lines.append("| Boss | Rank % | Best DPS/HPS | Total Kills | Rank Details |")
            lines.append("|------|--------|--------------|-------------|--------------|")
            
            for encounter in rankings:
                boss = encounter.get('encounter', {}).get('name', 'Unknown')
                rank_percent = encounter.get('rankPercent', 0)
                best_amount = encounter.get('bestAmount', 0)
                total_kills = encounter.get('totalKills', 0)
                rank_details = encounter.get('rankDetails', 'N/A')
                
                lines.append(f"| {boss} | {format_amount(rank_percent)}% | {format_int(best_amount)} | {total_kills} | {rank_details} |")
        else:
            lines.append("*No heroic boss rankings available*")
        
        lines.append("")
    
    # All Stars
    if mythic_data:
        lines.append("---\n")
        lines.append("## ⭐ All Stars Points\n")
        all_stars = mythic_data.get('allStars', [])
        
        if all_stars:
            lines.append("| Partition | Spec | Points | Possible | Rank % |")
            lines.append("|-----------|------|--------|----------|--------|")
            
            for star in all_stars:
                partition = star.get('partition', 'N/A')
                spec = star.get('spec', 'Unknown')
                points = star.get('points', 0)
                possible = star.get('possiblePoints', 0)
                rank_pct = star.get('rankPercent', 0)
                
                lines.append(f"| {partition} | {spec} | {format_amount(points)} | {format_amount(possible)} | {format_amount(rank_pct)}% |")
        else:
            lines.append("*No all-stars data available*")
        
        lines.append("")
    
    lines.append("---")
    
    return "\n".join(lines)

# Worker Function
def crawl_character(row, attempt=1):
    """Crawl all data for a single character"""
    server = row["Server"].strip()
    character = row["ID"].strip()
    role = row["Role"].strip()
    character_class = row["Class"].strip()
    
    console.print(f"[info]▶ Fetching {character}... (Attempt {attempt})[/info]")
    
    try:
        equipment_data, trinkets = get_character_equipment(server, character)
        ilvl = get_ilvl_from_blizzard(server, character)
        mplus_score = get_mplus_score(server, character)
        wcl_data = get_wcl_data_with_trinkets(server, character, role)
        
        blizzard_spec, blizzard_spec_icon = get_character_spec(server, character)
        
        if (wcl_data is None or ilvl == 0) and attempt < 3:
            console.print(f"[warning]⚠ Retrying {character}...[/warning]")
            time.sleep(2)
            return crawl_character(row, attempt + 1)
        
        if wcl_data is None:
            with open(FAILED_LOG, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {character} - WCL API error\n")
            console.print(f"[error]❌ {character} - WCL API failed[/error]")
            wcl_data = {}
        
        mythic_data = wcl_data.get('mythic', {}) if isinstance(wcl_data, dict) else wcl_data
        heroic_data = wcl_data.get('heroic', {}) if isinstance(wcl_data, dict) else {}
        
        all_stars = mythic_data.get('allStars', []) if mythic_data else []
        if not all_stars and heroic_data:
            all_stars = heroic_data.get('allStars', [])
        
        wcl_spec = all_stars[0].get('spec', blizzard_spec) if all_stars else blizzard_spec
        wcl_spec_icon = blizzard_spec_icon
        
        best_perf_avg = mythic_data.get('bestPerformanceAverage', "N/A") if mythic_data else "N/A"
        if best_perf_avg == "N/A" and heroic_data:
            best_perf_avg = heroic_data.get('bestPerformanceAverage', "N/A")
        
        os.makedirs(DETAIL_DIR, exist_ok=True)
        report_content = format_comprehensive_report(
            character, character_class, role, server, wcl_spec, wcl_spec_icon,
            equipment_data, trinkets, ilvl, mplus_score, wcl_data
        )
        with open(os.path.join(DETAIL_DIR, f"{character}.md"), "w", encoding="utf-8") as f:
            f.write(report_content)
        
        console.print(f"[success]✔ {character} complete! ({wcl_spec}, ilvl {ilvl}, {len(trinkets)} trinkets)[/success]")
        
        return [
            character,
            character_class,
            wcl_spec,
            ilvl,
            format_amount(mplus_score),
            format_amount(best_perf_avg) if best_perf_avg != "N/A" else "N/A"
        ]
        
    except Exception as e:
        console.print(f"[error]❌ Unexpected error for {character}: {e}[/error]")
        with open(FAILED_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {character} - Error: {str(e)}\n")
        return [character, character_class, "N/A", 0, "N/A", "N/A"]

def main():
    """Main execution"""
    start_time = time.time()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DETAIL_DIR, exist_ok=True)
    
    if os.path.exists(FAILED_LOG):
        os.remove(FAILED_LOG)
    
    if not os.path.exists(INPUT_FILE):
        console.print(f"[error]❌ Input file not found: {INPUT_FILE}[/error]")
        return
    
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        characters = list(reader)
    
    roster_num = len(characters)
    console.print(f"[bold cyan]🎮 Fetching data for {roster_num} players...[/bold cyan]\n")
    console.print(f"[bold green]✨ Now tracking trinkets per boss/dungeon![/bold green]\n")
    
    results = []
    
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("• {task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing...", total=roster_num)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(crawl_character, char) for char in characters]
            
            for future in futures:
                result = future.result()
                if result:
                    results.append(result)
                progress.update(task, advance=1)
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Class", "Spec", "ilvl", "M+", "WCL"])
        writer.writerows(results)
    
    elapsed = time.time() - start_time
    console.print(f"\n[success]✅ Crawling complete in {elapsed:.1f}s[/success]")
    console.print(f"[info]📁 Results saved to: {OUTPUT_FILE}[/info]")
    console.print(f"[info]📝 Detailed reports with trinket tracking in: {DETAIL_DIR}/[/info]")
    
    table = Table(title="WoW Character Summary", show_lines=True)
    table.add_column("ID", justify="left", style="cyan", no_wrap=True)
    table.add_column("Class", justify="left", style="magenta")
    table.add_column("Spec", justify="left", style="yellow")
    table.add_column("ilvl", justify="right", style="green")
    table.add_column("M+", justify="right", style="blue")
    table.add_column("WCL", justify="right", style="red")
    
    for row in results:
        char_id, char_class, spec, ilvl, mplus, wcl = row
        table.add_row(char_id, char_class, spec, str(ilvl), str(mplus), str(wcl))
    
    console.print(table)
    console.print("\n[success]🎉 All tasks completed![/success]")
    console.print("[info]💡 Trinket data is now included in detailed/*.md files[/info]")

if __name__ == "__main__":
    main()
