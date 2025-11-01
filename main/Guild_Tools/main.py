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

# Load environment variables from .env file
load_dotenv()

# ────────────────────────────────────────────────
# Settings
INPUT_FILE = "characters.csv"
OUTPUT_DIR = "logs"
DETAIL_DIR = "detailed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Player_data.csv")
FAILED_LOG = os.path.join(OUTPUT_DIR, "failed_characters.log")
PREVIOUS_FILE = os.path.join(OUTPUT_DIR, "previous_Player_data.csv")
WEEKLY_FILE = os.path.join(OUTPUT_DIR, "weekly_comparison.csv")

# API Credentials - Loaded from .env file
BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")
WCL_ACCESS_TOKEN = os.getenv("WCL_ACCESS_TOKEN")

if not all([BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET, WCL_ACCESS_TOKEN]):
    raise ValueError("❌ Missing API credentials! Please check your .env file.")

BLIZZARD_TOKEN_URL = "https://kr.battle.net/oauth/token"
REGION = os.getenv("REGION", "kr")
NAMESPACE = os.getenv("NAMESPACE", "profile-kr")

# Console Theme
theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "error": "bold red",
    "warning": "yellow"
})
console = Console(theme=theme)

# ────────────────────────────────────────────────
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
            console.print("[success]✅ Blizzard token obtained[/success]")
            return token
        except requests.exceptions.RequestException as e:
            console.print(f"[error]❌ Token fetch failed: {e}[/error]")
            return None

token_manager = TokenManager()

# ────────────────────────────────────────────────
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
            time.sleep(0.1)  # Rate limit protection
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
    if any(ord(c) > 128 for c in name):  # Korean characters
        return name
    return name.lower()

# ────────────────────────────────────────────────
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
        
        # Find active spec
        for spec_group in specializations:
            if spec_group.get("is_active", False):
                spec_info = spec_group.get("specialization", {})
                spec_name = spec_info.get("name", "Unknown")
                spec_id = spec_info.get("id", 0)
                
                # Get spec icon
                spec_icon = get_spec_icon(spec_id, token)
                
                return spec_name, spec_icon
        
        # Fallback to first spec if no active found
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
    """Get detailed equipment list from Blizzard API with item icons"""
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
            
            # Get icon URL from Blizzard media API
            icon_url = get_item_icon(item_id, token)
            
            equipment_list.append({
                "slot": slot_name,
                "name": item_name,
                "ilvl": item_level,
                "item_id": item_id,
                "icon": icon_url
            })
        
        return equipment_list
    except (KeyError, ValueError, TypeError) as e:
        console.print(f"[warning]⚠ Failed to parse equipment: {e}[/warning]")
        return []

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
        
        # Filter out cosmetic slots
        ilvls = []
        for item in equipped:
            slot_name = item.get("slot", {}).get("name", "")
            if slot_name not in ["속옷", "겉옷"]:  # Exclude shirt/tabard
                ilvls.append(item["level"]["value"])
        
        return round(sum(ilvls) / len(ilvls), 1) if ilvls else 0
    except (KeyError, ValueError, TypeError) as e:
        console.print(f"[warning]⚠ Failed to parse ilvl: {e}[/warning]")
        return 0

def get_mplus_score(server, character):
    """Get Mythic+ score from Raider.IO"""
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
    except (KeyError, ValueError, TypeError):
        return "N/A"

def get_wcl_data(server, character, role):
    """Get WarcraftLogs performance data"""
    metric = "hps" if role.lower() == "healer" else "dps"
    
    query = """
    query($name: String!, $server: String!, $region: String!, $metric: CharacterRankingMetricType!) {
      characterData {
        character(name: $name, serverSlug: $server, serverRegion: $region) {
          name
          zoneRankings(metric: $metric)
        }
      }
    }
    """
    
    variables = {
        "name": character,
        "server": server.lower(),
        "region": REGION,
        "metric": metric
    }
    
    headers = {
        "Authorization": f"Bearer {WCL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {"query": query, "variables": variables}
    
    resp = safe_request("POST", "https://www.warcraftlogs.com/api/v2/client",
                       headers=headers, json=payload)
    if not resp:
        return None
    
    try:
        data = resp.json()
        
        # Check for GraphQL errors
        if 'errors' in data:
            error_msg = data['errors'][0].get('message', 'Unknown') if data['errors'] else 'Unknown'
            console.print(f"[warning]⚠ WCL error: {error_msg}[/warning]")
            return None
        
        character_info = data.get('data', {}).get('characterData', {}).get('character')
        
        if not character_info:
            console.print(f"[warning]⚠ {character}@{server} not found in WCL (no logs)[/warning]")
            return {}  # Return empty dict for characters without logs
        
        return character_info.get('zoneRankings', {})
        
    except (KeyError, TypeError, ValueError) as e:
        console.print(f"[warning]⚠ WCL parse error: {e}[/warning]")
        return None

# ────────────────────────────────────────────────
# Formatting Functions

def format_comprehensive_report(character, character_class, role, server, wcl_spec, wcl_spec_icon,
                               equipment_data, ilvl, mplus_score, wcl_data):
    """Format comprehensive character report with all data including item IDs"""
    lines = []
    lines.append(f"# {character}")
    lines.append(f"**{wcl_spec} {character_class}** | **{role}** | **{server}**")
    lines.append(f"**SPEC_ICON:{wcl_spec_icon}**")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    lines.append("---\n")
    
    # ═══════════════════════════════════════
    # OVERVIEW SECTION
    # ═══════════════════════════════════════
    lines.append("## 📊 Overview\n")
    lines.append(f"- **Average Item Level:** {ilvl}")
    lines.append(f"- **Mythic+ Score:** {format_amount(mplus_score)}")
    
    best_perf_avg = wcl_data.get('bestPerformanceAverage') if wcl_data else None
    lines.append(f"- **WarcraftLogs Average:** {format_amount(best_perf_avg)}\n")
    
    # ═══════════════════════════════════════
    # EQUIPMENT SECTION (with item IDs)
    # ═══════════════════════════════════════
    lines.append("---\n")
    lines.append("## ⚔️ Equipment\n")
    
    if equipment_data:
        lines.append("| Slot | Item Name | Item Level | Icon |")
        lines.append("|------|-----------|------------|------|")
        
        for item in equipment_data:
            slot = item.get('slot', 'Unknown')
            name = item.get('name', 'Unknown')
            item_ilvl = item.get('ilvl', 0)
            icon_url = item.get('icon', '')
            # Store icon URL but display as hidden marker
            lines.append(f"| {slot} | {name} | {item_ilvl} | ICON:{icon_url} |")
    else:
        lines.append("*Equipment data not available*")
    
    lines.append("")
    
    # ═══════════════════════════════════════
    # WARCRAFTLOGS SECTION
    # ═══════════════════════════════════════
    lines.append("---\n")
    lines.append("## 🏆 WarcraftLogs Performance\n")
    
    if not wcl_data or wcl_data == {}:
        lines.append("*No raid logs found for this character*\n")
    else:
        # Best Performance Average
        best_perf_avg = wcl_data.get('bestPerformanceAverage')
        if best_perf_avg:
            lines.append(f"### Best Performance Average: **{format_amount(best_perf_avg)}**\n")
        
        # Boss Rankings
        lines.append("### 📋 Boss Rankings\n")
        rankings = wcl_data.get('rankings', [])
        
        if rankings:
            lines.append("| Boss | Rank % | Best DPS/HPS | Total Kills |")
            lines.append("|------|--------|--------------|-------------|")
            
            for encounter in rankings:
                boss = encounter.get('encounter', {}).get('name', 'Unknown')
                rank_percent = encounter.get('rankPercent', 0)
                best_amount = encounter.get('bestAmount', 0)
                total_kills = encounter.get('totalKills', 0)
                
                lines.append(f"| {boss} | {format_amount(rank_percent)}% | {format_int(best_amount)} | {total_kills} |")
        else:
            lines.append("*No boss rankings available*")
        
        lines.append("")
        
        # All Stars
        lines.append("### ⭐ All Stars Points\n")
        all_stars = wcl_data.get('allStars', [])
        
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
        
        # Rankings (Server/Region/World)
        lines.append("### 🌍 Rankings\n")
        
        if all_stars:
            lines.append("| Partition | Spec | Overall Rank | Region Rank | Server Rank |")
            lines.append("|-----------|------|--------------|-------------|-------------|")
            
            for partition in all_stars:
                div = partition.get('partition', 'N/A')
                spec = partition.get('spec', 'Unknown')
                rank = partition.get('rank', 0)
                total = partition.get('total', 0)
                region = partition.get('regionRank', 0)
                server_rank = partition.get('serverRank', 0)
                
                overall = f"{format_int(rank)} / {format_int(total)}" if rank and total else "N/A"
                lines.append(f"| {div} | {spec} | {overall} | {format_int(region)} | {format_int(server_rank)} |")
        else:
            lines.append("*No ranking data available*")
        
        lines.append("")
        
        # Median Performance
        median_perf = wcl_data.get('medianPerformanceAverage')
        if median_perf:
            lines.append(f"**Median Performance Average:** {format_amount(median_perf)}\n")
    
    lines.append("---")
    
    return "\n".join(lines)

# ────────────────────────────────────────────────
# Worker Function

def crawl_character(row, attempt=1):
    """Crawl all data for a single character"""
    server = row["Server"].strip()
    character = row["ID"].strip()
    role = row["Role"].strip()
    character_class = row["Class"].strip()
    
    console.print(f"[info]▶ Fetching {character}... (Attempt {attempt})[/info]")
    
    try:
        # Collect all data
        equipment_data = get_character_equipment(server, character)
        ilvl = get_ilvl_from_blizzard(server, character)
        mplus_score = get_mplus_score(server, character)
        wcl_data = get_wcl_data(server, character, role)
        
        # Get spec with icon from Blizzard API
        blizzard_spec, blizzard_spec_icon = get_character_spec(server, character)
        
        # Retry logic for failures
        if (wcl_data is None or ilvl == 0) and attempt < 3:
            console.print(f"[warning]⚠ Retrying {character}...[/warning]")
            time.sleep(2)
            return crawl_character(row, attempt + 1)
        
        # Handle WCL data
        if wcl_data is None:
            # Complete API failure
            with open(FAILED_LOG, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {character} - WCL API error\n")
            console.print(f"[error]❌ {character} - WCL API failed[/error]")
            wcl_data = {}  # Use empty dict for report generation
        
        # Extract spec from WCL or use Blizzard spec
        all_stars = wcl_data.get('allStars', [])
        wcl_spec = all_stars[0].get('spec', blizzard_spec) if all_stars else blizzard_spec
        wcl_spec_icon = blizzard_spec_icon  # Use Blizzard icon
        best_perf_avg = wcl_data.get('bestPerformanceAverage', "N/A")
        
        # Save comprehensive report
        os.makedirs(DETAIL_DIR, exist_ok=True)
        report_content = format_comprehensive_report(
            character, character_class, role, server, wcl_spec, wcl_spec_icon,
            equipment_data, ilvl, mplus_score, wcl_data
        )
        with open(os.path.join(DETAIL_DIR, f"{character}.md"), "w", encoding="utf-8") as f:
            f.write(report_content)
        
        console.print(f"[success]✔ {character} complete! ({wcl_spec}, ilvl {ilvl})[/success]")
        
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

# ────────────────────────────────────────────────
# Comparison Functions

def generate_weekly_comparison(current_file, previous_file, output_file):
    """Generate weekly comparison report"""
    if not os.path.exists(current_file):
        console.print(f"[error]❌ Current data file not found[/error]")
        return
    
    current_data = {}
    with open(current_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            current_data[row["ID"]] = row
    
    previous_data = {}
    if os.path.exists(previous_file):
        with open(previous_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                previous_data[row["ID"]] = row
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["ID", "Class", "Spec", "ilvl", "ilvl_change", "M+", "M+_change", "WCL", "WCL_change"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for char_id, curr in current_data.items():
            prev = previous_data.get(char_id, {})
            
            # Calculate changes
            try:
                ilvl_change = int(float(curr["ilvl"])) - int(float(prev.get("ilvl", curr["ilvl"]))) if prev else 0
            except:
                ilvl_change = 0
            
            try:
                mplus_curr = float(str(curr["M+"]).replace(",", ""))
                mplus_prev = float(str(prev.get("M+", curr["M+"])).replace(",", "")) if prev else mplus_curr
                mplus_change = mplus_curr - mplus_prev
            except:
                mplus_change = 0
            
            try:
                wcl_curr = float(str(curr["WCL"]).replace(",", ""))
                wcl_prev = float(str(prev.get("WCL", curr["WCL"])).replace(",", "")) if prev else wcl_curr
                wcl_change = wcl_curr - wcl_prev
            except:
                wcl_change = 0
            
            writer.writerow({
                "ID": char_id,
                "Class": curr["Class"],
                "Spec": curr["Spec"],
                "ilvl": curr["ilvl"],
                "ilvl_change": f"+{ilvl_change}" if ilvl_change > 0 else str(ilvl_change),
                "M+": curr["M+"],
                "M+_change": f"+{mplus_change:.1f}" if mplus_change > 0 else f"{mplus_change:.1f}",
                "WCL": curr["WCL"],
                "WCL_change": f"+{wcl_change:.1f}" if wcl_change > 0 else f"{wcl_change:.1f}"
            })
    
    console.print(f"[success]✅ Weekly comparison saved to {output_file}[/success]")
    
    # Backup current as previous
    import shutil
    shutil.copy(current_file, previous_file)
    console.print(f"[info]📦 Previous week data updated[/info]")

def print_console_summary(results):
    """Print summary table to console"""
    table = Table(title="WoW Character Summary", show_lines=True)
    table.add_column("ID", justify="left", style="cyan", no_wrap=True)
    table.add_column("Class", justify="left", style="magenta")
    table.add_column("Spec", justify="left", style="yellow")
    table.add_column("ilvl", justify="right", style="green")
    table.add_column("M+", justify="right", style="blue")
    table.add_column("WCL", justify="right", style="red")
    
    total_ilvl = 0
    total_mplus = 0
    total_wcl = 0
    count = 0
    
    for row in results:
        char_id, char_class, spec, ilvl, mplus, wcl = row
        table.add_row(char_id, char_class, spec, str(ilvl), str(mplus), str(wcl))
        count += 1
        
        try:
            total_ilvl += float(ilvl)
        except:
            pass
        try:
            total_mplus += float(str(mplus).replace(",", ""))
        except:
            pass
        try:
            total_wcl += float(str(wcl).replace(",", ""))
        except:
            pass
    
    console.print(table)
    
    if count > 0:
        avg_ilvl = total_ilvl / count
        avg_mplus = total_mplus / count
        avg_wcl = total_wcl / count
        console.print(f"\n[info]📊 Averages - ilvl: {avg_ilvl:.1f} | M+: {avg_mplus:.1f} | WCL: {avg_wcl:.1f}[/info]")

# ────────────────────────────────────────────────
# Main Function

def main():
    """Main execution"""
    start_time = time.time()
    
    # Setup
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DETAIL_DIR, exist_ok=True)
    
    # Clear failed log
    if os.path.exists(FAILED_LOG):
        os.remove(FAILED_LOG)
    
    # Load characters
    if not os.path.exists(INPUT_FILE):
        console.print(f"[error]❌ Input file not found: {INPUT_FILE}[/error]")
        return
    
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        characters = list(reader)
    
    roster_num = len(characters)
    console.print(f"[bold cyan]🎮 Fetching data for {roster_num} players...[/bold cyan]\n")
    
    results = []
    
    # Process with progress bar
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
    
    # Save results
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Class", "Spec", "ilvl", "M+", "WCL"])
        writer.writerows(results)
    
    elapsed = time.time() - start_time
    console.print(f"\n[success]✅ Crawling complete in {elapsed:.1f}s[/success]")
    console.print(f"[info]📁 Results saved to: {OUTPUT_FILE}[/info]")
    
    # Print summary
    print_console_summary(results)
    
    # Generate weekly comparison
    generate_weekly_comparison(OUTPUT_FILE, PREVIOUS_FILE, WEEKLY_FILE)
    
    console.print("\n[success]🎉 All tasks completed![/success]")

if __name__ == "__main__":
    main()
