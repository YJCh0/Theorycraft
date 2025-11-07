import csv
import os
import json
from datetime import datetime

# Complete Raid buff mapping - 11 essential buffs
RAID_BUFFS = {
    'battle_shout': {
        'name': 'Battle Shout',
        'classes': ['Warrior'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_warrior_battleshout.jpg'
    },
    'mark_of_the_wild': {
        'name': 'Mark of the Wild',
        'classes': ['Druid'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_nature_regeneration.jpg'
    },
    'arcane_intellect': {
        'name': 'Arcane Intellect',
        'classes': ['Mage'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_holy_magicalsentry.jpg'
    },
    'skyfury': {
        'name': 'Skyfury',
        'classes': ['Shaman'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/achievement_raidprimalist_windelemental.jpg'
    },
    'blessing_of_the_bronze': {
        'name': 'Blessing of the Bronze',
        'classes': ['Evoker'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_evoker_blessingofthebronze.jpg'
    },
    'hunters_mark': {
        'name': "Hunter's Mark",
        'classes': ['Hunter'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_hunter_markedfordeath.jpg'
    },
    'power_word_fortitude': {
        'name': 'Power Word: Fortitude',
        'classes': ['Priest'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_holy_wordfortitude.jpg'
    },
    'devotion_aura': {
        'name': 'devotion_aura',
        'classes': ['Paladin'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_holy_devotionaura.jpg'
    },
    'numbing_poison': {
        'name': 'numbing_poison',
        'classes': ['Rogue'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_nature_nullifydisease.jpg'
    },
    'mystic_touch': {
        'name': 'Mystic Touch',
        'classes': ['Monk'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_monk_sparring.jpg'
    },
    'chaos_brand': {
        'name': 'Chaos Brand',
        'classes': ['Demon Hunter', 'Demonhunter'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_demonhunter_empowerwards.jpg'
    },
    'healthstone': {
        'name': 'Healthstone',
        'classes': ['Warlock'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/warlock_-healthstone.jpg'
    },
    'death_grip': {
        'name': 'Death Grip',
        'classes': ['Deathknight', 'Death Knight'],
        'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_deathknight_strangulate.jpg'
    }
}
def parse_wcl_from_markdown(content):
    """Extract WCL data from markdown content for both difficulties"""
    wcl_data = {
        'has_logs': False,
        'mythic': {'best_performance': 'N/A', 'boss_rankings': []},
        'heroic': {'best_performance': 'N/A', 'boss_rankings': []},
        'all_stars': []
    }
    
    lines = content.split('\n')
    current_difficulty = None
    in_boss_table = False
    in_allstars_table = False
    
    for i, line in enumerate(lines):
        if '## 🏆 WarcraftLogs Performance - Mythic' in line:
            current_difficulty = 'mythic'
            wcl_data['has_logs'] = True
            continue
        
        if '## 🏆 WarcraftLogs Performance - Heroic' in line:
            current_difficulty = 'heroic'
            wcl_data['has_logs'] = True
            continue
        
        if '## ⭐ All Stars Points' in line:
            current_difficulty = None
            in_allstars_table = True
            in_boss_table = False
            continue
        
        if current_difficulty:
            if 'Best Performance Average:' in line:
                try:
                    wcl_data[current_difficulty]['best_performance'] = line.split('**')[1].strip()
                except:
                    pass
            
            if '### 📋 Boss Rankings' in line:
                in_boss_table = True
                continue
            
            if in_boss_table and line.startswith('|') and '---' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 4 and parts[0] not in ['Boss', '']:
                    try:
                        boss_entry = {
                            'boss': parts[0],
                            'rank_percent': parts[1].replace('%', '').strip(),
                            'best_amount': int(parts[2].replace(',', '')),
                            'total_kills': int(parts[3])
                        }
                        # Check if rank details column exists
                        if len(parts) >= 5:
                            boss_entry['rank_details'] = parts[4]
                        
                        wcl_data[current_difficulty]['boss_rankings'].append(boss_entry)
                    except:
                        pass
            
            if line.startswith('---') or line.startswith('##'):
                in_boss_table = False
        
        if in_allstars_table and line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 5 and parts[0] not in ['Partition', '']:
                try:
                    wcl_data['all_stars'].append({
                        'partition': parts[0],
                        'spec': parts[1],
                        'points': float(parts[2].replace(',', '')),
                        'possible': float(parts[3].replace(',', '')),
                        'rank_percent': float(parts[4].replace('%', '').strip())
                    })
                except:
                    pass
    
    return wcl_data

def parse_trinkets_from_markdown(content):
    """Extract trinket data from markdown"""
    trinkets = []
    lines = content.split('\n')
    in_trinket_section = False
    
    for line in lines:
        if '## 🎯 Current Trinkets' in line:
            in_trinket_section = True
            continue
        
        if in_trinket_section and line.startswith('##'):
            break
        
        if in_trinket_section and line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4 and parts[0] not in ['Trinket', '']:
                trinket_name = parts[0]
                ilvl = parts[1]
                upgrade = parts[2]
                icon_part = parts[3]
                
                icon_url = ''
                if icon_part.startswith('TRINKET_ICON:'):
                    icon_url = icon_part.replace('TRINKET_ICON:', '').strip()
                
                trinkets.append({
                    'name': trinket_name,
                    'ilvl': ilvl,
                    'upgrade': upgrade,
                    'icon': icon_url
                })
    
    return trinkets

def parse_equipment_from_markdown(content):
    """Extract equipment from markdown"""
    equipment = []
    lines = content.split('\n')
    in_equipment = False
    
    for line in lines:
        if '## ⚔️ Equipment' in line:
            in_equipment = True
            continue
        
        if in_equipment and line.startswith('##'):
            break
        
        if in_equipment and line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 5 and parts[0] not in ['Slot', '']:
                icon_part = parts[4]
                icon_url = ''
                if icon_part.startswith('ICON:'):
                    icon_url = icon_part.replace('ICON:', '').strip()
                
                equipment.append({
                    'slot': parts[0],
                    'name': parts[1],
                    'ilvl': parts[2],
                    'upgrade': parts[3],
                    'icon': icon_url
                })
    
    return equipment

def get_rio_color(score):
    """Get Raider.IO color based on score"""
    if score >= 3500: return '#ff8000'
    elif score >= 3000: return '#a335ee'
    elif score >= 2500: return '#0070dd'
    elif score >= 2000: return '#1eff00'
    elif score >= 1500: return '#ffffff'
    else: return '#808080'

def wcl_color(s):
    if s == 100: return '#e6cc80'
    elif s >= 99: return '#e367a5'
    elif s >= 95: return '#ff8000'
    elif s >= 75: return '#a335ee'
    elif s >= 50: return '#0070dd'
    elif s >= 25: return '#1eff00'
    return '#808080'

def check_missing_buffs(characters):
    """Check which raid buffs are missing from roster"""
    present_classes = set()
    for char in characters:
        char_class = char['Class'].strip()
        present_classes.add(char_class)
    
    missing_buffs = []
    present_buffs = []
    
    for buff_key, buff_info in RAID_BUFFS.items():
        buff_classes = set(buff_info['classes'])
        if buff_classes.isdisjoint(present_classes):
            missing_buffs.append(buff_info)
        else:
            present_buffs.append(buff_info)
    
    return present_buffs, missing_buffs

def generate_html_dashboard(csv_file, output_file="dashboard.html", detailed_dir="detailed"):
    """Generate dashboard with trinket tracking and proper icons"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🎨 Generating enhanced dashboard v3...")
    
    # Load history
    try:
        from history_tracker import get_guild_average_history, get_top_improvers
        guild_history = get_guild_average_history()
        top_improvers = get_top_improvers(7)
    except:
        guild_history = {'dates': [], 'avg_ilvl': [], 'avg_mplus': [], 'avg_wcl': []}
        top_improvers = []
    
    # Load M+ data
    mplus_data = {}
    if os.path.exists("logs/mplus_enhanced.json"):
        with open("logs/mplus_enhanced.json", 'r') as f:
            mplus_data = json.load(f)
    
    # Read characters
    characters = []
    character_specs = {}
    character_details = {}
    wcl_details = {}
    character_servers = {}
    character_trinkets = {}

    with open(csv_file, 'r', encoding='utf-8') as f:
        characters = list(csv.DictReader(f))
    
    # Parse detailed files
    if os.path.exists(detailed_dir):
        for fname in os.listdir(detailed_dir):
            if fname.endswith('.md'):
                name = fname[:-3]
                with open(os.path.join(detailed_dir, fname), 'r', encoding='utf-8') as f:
                    content = f.read()
                    character_details[name] = content
                    
                    # Extract data
                    for line in content.split('\n'):
                        if line.startswith('**SPEC_ICON:'):
                            character_specs[name] = line.replace('**SPEC_ICON:', '').replace('**', '').strip()
                        if '|' in line and '**' in line:
                            parts = line.split('|')
                            if len(parts) >= 4:
                                server_part = parts[-2].strip()
                                if server_part.startswith('**') and server_part.endswith('**'):
                                    character_servers[name] = server_part.replace('**', '').strip()
                    
                    wcl_details[name] = parse_wcl_from_markdown(content)
                    character_trinkets[name] = parse_trinkets_from_markdown(content)
    
    # Check raid buffs
    present_buffs, missing_buffs = check_missing_buffs(characters)
    
    # Stats
    total = len(characters)
    ilvls = [float(c['ilvl']) for c in characters if c['ilvl'] != 'N/A']
    mplus_scores = [float(str(c['M+']).replace(',', '')) for c in characters if c['M+'] != 'N/A']
    wcl_scores = [float(str(c['WCL']).replace(',', '')) for c in characters if c['WCL'] != 'N/A']
    
    avg_ilvl = sum(ilvls)/len(ilvls) if ilvls else 0
    avg_mplus = sum(mplus_scores)/len(mplus_scores) if mplus_scores else 0
    avg_wcl = sum(wcl_scores)/len(wcl_scores) if wcl_scores else 0
    
    # Chart data
    names = [c['ID'] for c in characters]
    ilvl_data = [float(c['ilvl']) if c['ilvl']!='N/A' else 0 for c in characters]
    mplus_data_chart = [float(str(c['M+']).replace(',','')) if c['M+']!='N/A' else 0 for c in characters]
    
    # Class colors
    class_colors = {
        'Deathknight':'#C41E3A','Demon Hunter':'#A330C9','Druid':'#FF7C0A',
        'Evoker':'#33937F','Hunter':'#AAD372','Mage':'#3FC7EB',
        'Monk':'#00FF98','Paladin':'#F48CBA','Priest':'#FFFFFF',
        'Rogue':'#FFF468','Shaman':'#0070DD','Warlock':'#8788EE',
        'Warrior':'#C69B6D','Demonhunter':'#A330C9'
    }
    classes = [c['Class'] for c in characters]
    colors = [class_colors.get(c,'#667eea') for c in classes]
    
    # WCL filtered data
    wcl_filtered_names = []
    wcl_filtered_data = []
    wcl_filtered_colors = []
    for c in characters:
        try:
            wcl_val = float(str(c['WCL']).replace(',',''))
            if wcl_val > 0:
                wcl_filtered_names.append(c['ID'])
                wcl_filtered_data.append(wcl_val)
                char_color = class_colors.get(c['Class'], '#667eea')
                wcl_filtered_colors.append(char_color)
        except:
            pass
    
    # Start HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guild Dashboard v3</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}}
.container{{max-width:1400px;margin:0 auto}}
header{{text-align:center;color:#fff;margin-bottom:40px;padding:20px}}
h1{{font-size:3em;text-shadow:2px 2px 4px rgba(0,0,0,0.3)}}
h2{{font-size:1.8em;margin-bottom:20px}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}}
.stat-card{{background:#fff;border-radius:15px;padding:25px;box-shadow:0 10px 30px rgba(0,0,0,.2);transition:transform .3s}}
.stat-card:hover{{transform:translateY(-5px)}}
.value{{font-size:2.5em;font-weight:bold;color:#667eea}}
.tab-container{{background:#fff;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.2);margin-bottom:40px;overflow:hidden}}
.tab-nav{{display:flex;background:#f0f0f0;border-bottom:2px solid #667eea}}
.tab-btn{{flex:1;padding:20px;background:none;border:none;cursor:pointer;font-size:1.1em;font-weight:600;color:#666;transition:all .3s;position:relative}}
.tab-btn:hover{{background:rgba(102,126,234,.1)}}
.tab-btn.active{{background:#fff;color:#667eea}}
.tab-btn.active::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:#667eea}}
.tab-content{{display:none;padding:30px}}
.tab-content.active{{display:block}}
.raid-buffs{{display:flex;gap:15px;flex-wrap:wrap;margin:20px 0;padding:20px;background:#f8f9fa;border-radius:10px}}
.buff-icon{{position:relative;width:48px;height:48px;border-radius:8px;border:3px solid #28a745;transition:all .3s}}
.buff-icon.missing{{opacity:0.3;border-color:#dc3545;filter:grayscale(100%)}}
.buff-icon img{{width:100%;height:100%;border-radius:6px}}
.buff-tooltip{{position:absolute;bottom:110%;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.9);color:#fff;padding:8px 12px;border-radius:6px;font-size:0.85em;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .3s;z-index:1000}}
.buff-icon:hover .buff-tooltip{{opacity:1}}
.chart-container{{position:relative;height:600px;padding:20px;background:#fff;border-radius:10px;border:2px solid #e0e0e0}}
.sort-controls{{display:flex;gap:15px;margin-bottom:20px;flex-wrap:wrap}}
.sort-btn{{padding:10px 20px;background:#f0f0f0;border:2px solid #667eea;border-radius:8px;cursor:pointer;font-weight:600;color:#667eea;transition:all .3s}}
.sort-btn:hover{{background:#667eea;color:#fff}}
.sort-btn.active{{background:#667eea;color:#fff}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}}
th{{background:#667eea;color:#fff;padding:15px;text-align:left;font-weight:600}}
td{{padding:12px 15px;border-bottom:1px solid #eee}}
tr:hover{{background:#f8f9ff}}
.profile-link{{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;margin:0 2px;border-radius:6px;transition:all .3s;text-decoration:none}}
.profile-link img{{width:20px;height:20px}}
.profile-link:hover{{transform:translateY(-2px);box-shadow:0 4px 8px rgba(0,0,0,0.2)}}
.armory-link{{background:#0070dd}}
.raiderio-link{{background:#667eea}}
.wcl-link{{background:#ff8000}}
.clickable{{cursor:pointer;color:#667eea;font-weight:600;text-decoration:none;transition:color .3s}}
.clickable:hover{{color:#764ba2;text-decoration:underline}}
.badge{{display:inline-block;padding:5px 12px;border-radius:12px;font-size:.85em;font-weight:600;white-space:nowrap}}
.trinket-display{{display:flex;gap:15px;margin:20px 0;padding:15px;background:#fff;border-radius:10px;border:2px solid #667eea}}
.trinket-item{{display:flex;align-items:center;gap:10px;padding:10px;background:#f8f9fa;border-radius:8px;flex:1}}
.trinket-item img{{width:48px;height:48px;border-radius:6px;border:2px solid #667eea}}
.modal{{display:none;position:fixed;z-index:1000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.7);animation:fadeIn .3s}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
.modal-content{{background:#fff;margin:30px auto;padding:0;border-radius:15px;width:95%;max-width:1200px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.3)}}
.modal-header{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:25px 30px;position:sticky;top:0;z-index:1001;display:flex;justify-content:space-between;align-items:center}}
.modal-body{{padding:30px}}
.close{{color:#fff;font-size:32px;font-weight:bold;cursor:pointer;transition:transform .3s}}
.close:hover{{transform:scale(1.1)}}
.char-section{{background:#f8f9fa;border-radius:15px;padding:25px;margin-bottom:30px;border:2px solid #e0e0e0}}
footer{{text-align:center;color:#fff;margin-top:40px;padding:20px}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>⚔️ Guild Dashboard</h1>
<p style="font-size:1.2em;margin-top:10px">{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</header>

<div class="stats-grid">
<div class="stat-card"><h3>👥 Total Members</h3><div class="value">{total}</div></div>
<div class="stat-card"><h3>⚔️ Average ilvl</h3><div class="value">{avg_ilvl:.1f}</div></div>
<div class="stat-card"><h3>🏔️ Average M+</h3><div class="value">{avg_mplus:.1f}</div></div>
<div class="stat-card"><h3>📈 Average WCL</h3><div class="value">{avg_wcl:.1f}</div></div>
</div>

<div class="tab-container">
<div class="tab-nav">
<button class="tab-btn active" data-tab="overview">📊 Overview</button>
<button class="tab-btn" data-tab="roster">📋 Roster</button>
<button class="tab-btn" data-tab="charts">📈 Charts</button>
<button class="tab-btn" data-tab="mplus">🏔️ M+ Details</button>
<button class="tab-btn" data-tab="raiding">🏆 Raiding</button>
</div>

<div id="overview" class="tab-content active">
<h2>Guild Progress Trends</h2>
<div class="chart-container"><canvas id="trendChart"></canvas></div>
<h2 style="margin-top:40px">🏆 Top Improvers (Last 7 Days)</h2>
<table style="margin-top:20px"><thead><tr><th style="width:80px">Rank</th><th>Character</th><th>Class & Spec</th><th>ilvl</th><th>M+</th><th>WCL</th></tr></thead><tbody>
"""
    
    # Top Improvers
    if top_improvers:
        for i, p in enumerate(top_improvers[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            html_content += f'<tr><td style="text-align:center;font-size:1.2em">{medal}</td><td><b>{p["name"]}</b></td><td>{p["spec"]} {p["class"]}</td><td style="color:#28a745;font-weight:600">+{p["ilvl_gain"]:.1f}</td><td style="color:#28a745;font-weight:600">+{p["mplus_gain"]:.0f}</td><td style="color:#28a745;font-weight:600">+{p["wcl_gain"]:.1f}</td></tr>'
    else:
        html_content += '<tr><td colspan="6" style="text-align:center;padding:40px;color:#999">Need at least 2 snapshots</td></tr>'
    
    html_content += """
</tbody></table>
</div>

<div id="roster" class="tab-content">
<h2>Character Roster</h2>

<div class="raid-buffs">
<h3 style="width:100%;margin-bottom:15px;color:#667eea">🎯 Raid Buff Coverage (11 Essential Buffs)</h3>
"""
    
    # Raid buff icons
    all_buffs = present_buffs + missing_buffs
    for buff in all_buffs:
        is_missing = buff in missing_buffs
        missing_class = " missing" if is_missing else ""
        status = "❌ Missing" if is_missing else "✅ Present"
        html_content += f'<div class="buff-icon{missing_class}"><img src="{buff["icon"]}" alt="{buff["name"]}"><div class="buff-tooltip">{buff["name"]}<br>{status}</div></div>'
    
    html_content += """
</div>

<div class="sort-controls">
<button class="sort-btn active" data-sort="name">📝 Name</button>
<button class="sort-btn" data-sort="ilvl">⚔️ ilvl</button>
<button class="sort-btn" data-sort="mplus">🏔️ M+</button>
<button class="sort-btn" data-sort="wcl">📈 WCL</button>
</div>

<table id="rosterTable"><thead><tr><th>Character</th><th>Class</th><th>Spec</th><th>ilvl</th><th>M+</th><th>WCL</th><th>Links</th></tr></thead><tbody>
"""
    
    # Roster data
    roster_data = []
    for c in characters:
        name = c['ID']
        has_detail = name in character_details
        spec_icon = character_specs.get(name, '')
        server = character_servers.get(name, 'azshara')
        
        # Profile links with proper logos
        armory_url = f"https://worldofwarcraft.blizzard.com/ko-kr/character/kr/{server.lower()}/{name.lower()}"
        raiderio_url = f"https://raider.io/characters/kr/{server}/{name}"
        wcl_url = f"https://www.warcraftlogs.com/character/kr/{server.lower()}/{name}"
        
        # Use SVG icons for better quality
        links_html = f'<a href="{armory_url}" target="_blank" title="Armory" class="profile-link armory-link"><img src="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'white\'%3E%3Cpath d=\'M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z\'/%3E%3C/svg%3E" alt="Armory"></a>'
        links_html += f'<a href="{raiderio_url}" target="_blank" title="Raider.IO" class="profile-link raiderio-link"><img src="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'white\'%3E%3Cpath d=\'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z\'/%3E%3C/svg%3E" alt="RIO"></a>'
        links_html += f'<a href="{wcl_url}" target="_blank" title="Warcraft Logs" class="profile-link wcl-link"><img src="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'white\'%3E%3Cpath d=\'M3 3v18h18V3H3zm16 16H5V5h14v14zM7 12h2v5H7zm4-3h2v8h-2zm4-3h2v11h-2z\'/%3E%3C/svg%3E" alt="WCL"></a>'
        
        # M+ badge
        try:
            mp = float(str(c['M+']).replace(',',''))
            mp_color = get_rio_color(mp)
            mp_badge = f'<span class="badge" style="background:{mp_color};color:#fff">{mp:.0f}</span>'
        except:
            mp = 0
            mp_badge = '<span class="badge" style="background:#808080;color:#fff">N/A</span>'
        
        # WCL badge
        try:
            wc = float(str(c['WCL']).replace(',',''))
            wc_col = wcl_color(wc)
            wc_badge = f'<span class="badge" style="background:{wc_col};color:#fff">{wc:.1f}</span>'
        except:
            wc = 0
            wc_badge = '<span class="badge" style="background:#808080;color:#fff">N/A</span>'
        
        try:
            ilvl_val = float(c['ilvl'])
        except:
            ilvl_val = 0
        
        roster_data.append({
            'name': name,
            'class': c['Class'],
            'spec': c['Spec'],
            'spec_icon': spec_icon,
            'ilvl': ilvl_val,
            'ilvl_display': c['ilvl'],
            'mplus': mp,
            'mplus_badge': mp_badge,
            'wcl': wc,
            'wcl_badge': wc_badge,
            'has_detail': has_detail,
            'links': links_html
        })
    
    # Initial display
    roster_data.sort(key=lambda x: x['name'])
    
    for rd in roster_data:
        spec_disp = f'<img src="{rd["spec_icon"]}" style="width:28px;height:28px;vertical-align:middle;margin-right:8px;border-radius:4px;border:2px solid #667eea" onerror="this.style.display=\'none\'"> {rd["spec"]}' if rd["spec_icon"] else rd["spec"]
        name_disp = f'<a href="#" class="clickable" onclick="showChar(\'{rd["name"]}\');return false">{rd["name"]}</a>' if rd["has_detail"] else f'<b>{rd["name"]}</b>'
        
        html_content += f'<tr><td>{name_disp}</td><td>{rd["class"]}</td><td>{spec_disp}</td><td><b>{rd["ilvl_display"]}</b></td><td>{rd["mplus_badge"]}</td><td>{rd["wcl_badge"]}</td><td>{rd["links"]}</td></tr>'
    
    html_content += """
</tbody></table>
</div>

<div id="charts" class="tab-content">
<h2>📊 Item Level Distribution</h2>
<div class="chart-container"><canvas id="ilvlChart"></canvas></div>
<h2 style="margin-top:40px">🏔️ M+ Score Distribution</h2>
<div class="chart-container"><canvas id="mplusChart"></canvas></div>
<h2 style="margin-top:40px">📈 WCL Performance Distribution</h2>
<div class="chart-container"><canvas id="wclChart"></canvas></div>
</div>

<div id="mplus" class="tab-content">
<h2 style="margin-bottom:30px">🏔️ Mythic+ Recent Runs with Trinket Usage</h2>
<p style="color:#666;margin-bottom:20px">📊 Note: Trinket data shown is current equipped trinkets. Per-dungeon tracking coming soon!</p>
"""
    
    # M+ Tab with trinket display
    if mplus_data:
        sorted_m = sorted([(n, d) for n, d in mplus_data.items() if d], 
                         key=lambda x: x[1].get("character", {}).get("score", 0), reverse=True)
        
        for name, data in sorted_m:
            ci = data.get("character", {})
            runs = data.get("best_runs", [])
            if not runs:
                continue
            
            score = ci.get("score", 0)
            score_color = get_rio_color(score)
            
            trinkets = character_trinkets.get(name, [])
            
            timed_runs = len([r for r in runs if r.get('timed', False)])
            avg_key_level = sum([r.get('level', 0) for r in runs]) / len(runs) if runs else 0
            
            html_content += f'<div class="char-section">'
            html_content += f'<div style="display:flex;align-items:center;margin-bottom:20px">'
            if ci.get("thumbnail"):
                html_content += f'<img src="{ci["thumbnail"]}" style="width:80px;height:80px;border-radius:10px;margin-right:20px;border:3px solid #667eea" onerror="this.style.display=\'none\'">'
            html_content += f'<div style="flex:1"><h3>{ci.get("name", name)}</h3><div style="display:flex;gap:15px;margin-top:10px;flex-wrap:wrap"><span class="badge">{ci.get("spec", "")} {ci.get("class", "")}</span><span class="badge">ilvl {ci.get("ilvl", 0)}</span><span class="badge" style="background:{score_color};color:#fff">M+ {score:.0f}</span></div></div></div>'
            
            html_content += f'<div style="background:#e3f2fd;padding:12px;border-radius:8px;margin-bottom:15px;border-left:4px solid #2196f3"><strong>📊 Quick Stats:</strong> {timed_runs}/{len(runs)} timed | Avg Key: +{avg_key_level:.1f}</div>'
            
            # Trinkets
            if trinkets:
                html_content += '<div class="trinket-display"><strong style="width:100%;margin-bottom:10px;display:block;color:#667eea">🎯 Current Trinkets:</strong>'
                for trinket in trinkets:
                    if trinket['icon']:
                        html_content += f'<div class="trinket-item"><img src="{trinket["icon"]}" onerror="this.style.display=\'none\'"><div><div style="font-weight:600;font-size:0.9em">{trinket["name"]}</div><div style="font-size:0.85em;color:#666">ilvl {trinket["ilvl"]} | {trinket["upgrade"]}</div></div></div>'
                html_content += '</div>'
            
            html_content += '</div>'
    else:
        html_content += '<div style="text-align:center;padding:80px;background:#f8f9fa;border-radius:15px"><h2 style="color:#999">📊 No M+ Data</h2><p style="color:#666;margin-top:15px">Run <code>python mplus_enhanced.py</code></p></div>'
    
    html_content += """
</div>

<div id="raiding" class="tab-content">
<h2 style="margin-bottom:20px">🏆 Warcraft Logs Performance with Raid Trinkets</h2>
<div class="sort-controls" style="margin-bottom:30px">
<button class="sort-btn active" data-difficulty="mythic">⚔️ Mythic</button>
<button class="sort-btn" data-difficulty="heroic">🛡️ Heroic</button>
</div>
"""
    
    if wcl_details:
        sorted_wcl = sorted([(name, data, next((c for c in characters if c['ID'] == name), None)) 
                            for name, data in wcl_details.items() if data.get('has_logs')],
                           key=lambda x: float(str(x[2]['WCL']).replace(',', '')) if x[2] and x[2]['WCL'] != 'N/A' else 0,
                           reverse=True)
        
        for name, wcl_data, char_info in sorted_wcl:
            if not char_info:
                continue
            
            spec_icon = character_specs.get(name, '')
            server = character_servers.get(name, 'azshara')
            trinkets = character_trinkets.get(name, [])
            
            mythic_data = wcl_data.get('mythic', {})
            mythic_perf = mythic_data.get('best_performance', 'N/A')
            mythic_bosses = mythic_data.get('boss_rankings', [])
            
            heroic_data = wcl_data.get('heroic', {})
            heroic_perf = heroic_data.get('best_performance', 'N/A')
            heroic_bosses = heroic_data.get('boss_rankings', [])
            
            mythic_perf_color = '#808080'
            heroic_perf_color = '#808080'
            
            try:
                if mythic_perf != 'N/A':
                    mythic_perf_color = wcl_color(float(str(mythic_perf).replace(',', '')))
            except:
                pass
            
            try:
                if heroic_perf != 'N/A':
                    heroic_perf_color = wcl_color(float(str(heroic_perf).replace(',', '')))
            except:
                pass
            
            html_content += f'<div class="char-section"><div style="display:flex;align-items:center;margin-bottom:20px">'
            if spec_icon:
                html_content += f'<img src="{spec_icon}" style="width:80px;height:80px;border-radius:10px;margin-right:20px;border:3px solid #667eea" onerror="this.style.display=\'none\'">'
            html_content += f'<div style="flex:1"><h3>{name}</h3><div style="display:flex;gap:15px;margin-top:10px;flex-wrap:wrap"><span class="badge">{char_info["Spec"]} {char_info["Class"]}</span><span class="badge" style="background:{mythic_perf_color};color:#fff">⚔️ M: {mythic_perf}</span><span class="badge" style="background:{heroic_perf_color};color:#fff">🛡️ H: {heroic_perf}</span></div></div></div>'
            
            # Trinkets for raiding
            if trinkets:
                html_content += '<div class="trinket-display"><strong style="width:100%;margin-bottom:10px;display:block;color:#667eea">🎯 Raid Trinkets:</strong>'
                for trinket in trinkets:
                    if trinket['icon']:
                        html_content += f'<div class="trinket-item"><img src="{trinket["icon"]}" onerror="this.style.display=\'none\'"><div><div style="font-weight:600;font-size:0.9em">{trinket["name"]}</div><div style="font-size:0.85em;color:#666">ilvl {trinket["ilvl"]} | {trinket["upgrade"]}</div></div></div>'
                html_content += '</div>'
            
            # Mythic bosses
            if mythic_bosses:
                html_content += '<div class="difficulty-mythic"><h4 style="margin:20px 0 15px 0;color:#a335ee">⚔️ Mythic Bosses</h4>'
                for boss in mythic_bosses:
                    boss_name = boss.get('boss', 'Unknown')
                    rank_pct = boss.get('rank_percent', 0)
                    best_amount = boss.get('best_amount', 0)
                    kills = boss.get('total_kills', 0)
                    rank_details = boss.get('rank_details', '')
                    
                    try:
                        rank_val = float(rank_pct)
                        boss_color = wcl_color(rank_val)
                    except:
                        rank_val = 0
                        boss_color = '#808080'
                    
                    # Format rank details display
                    rank_info = f'<div style="color:#666;font-size:0.85em;margin-top:3px">📊 Rank: {rank_details}</div>' if rank_details else ''
                    
                    html_content += f'<div style="background:#f8f9fa;padding:20px;border-radius:10px;margin-bottom:15px;border-left:4px solid {boss_color}"><div style="display:flex;justify-content:space-between;margin-bottom:10px"><div><strong>{boss_name}</strong><div style="color:#666;font-size:0.9em;margin-top:5px">💀 {kills} kills | 📊 Best: {best_amount:,}</div>{rank_info}</div><div style="font-size:1.8em;font-weight:bold;color:{boss_color}">{rank_pct}%</div></div><div style="height:30px;background:#e0e0e0;border-radius:6px;overflow:hidden"><div style="width:{rank_val}%;height:100%;background:{boss_color};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600;transition:width .8s">{rank_pct}%</div></div></div>'
                html_content += '</div>'
            
            # Heroic bosses
            if heroic_bosses:
                html_content += '<div class="difficulty-heroic" style="display:none"><h4 style="margin:20px 0 15px 0;color:#0070dd">🛡️ Heroic Bosses</h4>'
                for boss in heroic_bosses:
                    boss_name = boss.get('boss', 'Unknown')
                    rank_pct = boss.get('rank_percent', 0)
                    best_amount = boss.get('best_amount', 0)
                    kills = boss.get('total_kills', 0)
                    rank_details = boss.get('rank_details', '')
                    
                    try:
                        rank_val = float(rank_pct)
                        boss_color = wcl_color(rank_val)
                    except:
                        rank_val = 0
                        boss_color = '#808080'
                    
                    rank_info = f'<div style="color:#666;font-size:0.85em;margin-top:3px">📊 Rank: {rank_details}</div>' if rank_details else ''
                    
                    html_content += f'<div style="background:#f8f9fa;padding:20px;border-radius:10px;margin-bottom:15px;border-left:4px solid {boss_color}"><div style="display:flex;justify-content:space-between;margin-bottom:10px"><div><strong>{boss_name}</strong><div style="color:#666;font-size:0.9em;margin-top:5px">💀 {kills} kills | 📊 Best: {best_amount:,}</div>{rank_info}</div><div style="font-size:1.8em;font-weight:bold;color:{boss_color}">{rank_pct}%</div></div><div style="height:30px;background:#e0e0e0;border-radius:6px;overflow:hidden"><div style="width:{rank_val}%;height:100%;background:{boss_color};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600;transition:width .8s">{rank_pct}%</div></div></div>'
                html_content += '</div>'
            
            html_content += '</div>'
    else:
        html_content += '<div style="text-align:center;padding:80px"><h2 style="color:#999">📊 No Raid Data</h2></div>'
    
    html_content += f"""
</div>
</div>

<div id="modal" class="modal" onclick="if(event.target==this)closeModal()">
<div class="modal-content">
<div class="modal-header">
<h2 id="modalTitle">Character Details</h2>
<span class="close" onclick="closeModal()">&times;</span>
</div>
<div class="modal-body" id="modalBody"></div>
</div>
</div>

<footer>
<p style="font-size:1.2em;font-weight:600">두부킴의 유기견들</p>
<p style="margin-top:10px;opacity:0.8">Generated with ❤️</p>
</footer>
</div>

<script>
const details = {json.dumps(character_details)};
const rosterData = {json.dumps(roster_data)};

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', function() {{
        const targetTab = this.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        document.getElementById(targetTab).classList.add('active');
    }});
}});

// Roster sorting
document.querySelectorAll('.sort-btn[data-sort]').forEach(btn => {{
    btn.addEventListener('click', function() {{
        const sortBy = this.dataset.sort;
        document.querySelectorAll('.sort-btn[data-sort]').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        
        let sorted = [...rosterData];
        if (sortBy === 'name') sorted.sort((a, b) => a.name.localeCompare(b.name));
        else if (sortBy === 'ilvl') sorted.sort((a, b) => b.ilvl - a.ilvl);
        else if (sortBy === 'mplus') sorted.sort((a, b) => b.mplus - a.mplus);
        else if (sortBy === 'wcl') sorted.sort((a, b) => b.wcl - a.wcl);
        
        const tbody = document.querySelector('#rosterTable tbody');
        tbody.innerHTML = '';
        sorted.forEach(rd => {{
            const specDisp = rd.spec_icon ? 
                `<img src="${{rd.spec_icon}}" style="width:28px;height:28px;vertical-align:middle;margin-right:8px;border-radius:4px;border:2px solid #667eea" onerror="this.style.display='none'"> ${{rd.spec}}` : 
                rd.spec;
            const nameDisp = rd.has_detail ? 
                `<a href="#" class="clickable" onclick="showChar('${{rd.name}}');return false">${{rd.name}}</a>` : 
                `<b>${{rd.name}}</b>`;
            tbody.innerHTML += `<tr><td>${{nameDisp}}</td><td>${{rd.class}}</td><td>${{specDisp}}</td><td><b>${{rd.ilvl_display}}</b></td><td>${{rd.mplus_badge}}</td><td>${{rd.wcl_badge}}</td><td>${{rd.links}}</td></tr>`;
        }});
    }});
}});

// Difficulty switching
document.querySelectorAll('.sort-btn[data-difficulty]').forEach(btn => {{
    btn.addEventListener('click', function() {{
        const diff = this.dataset.difficulty;
        document.querySelectorAll('.sort-btn[data-difficulty]').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        document.querySelectorAll('.difficulty-mythic').forEach(el => el.style.display = diff === 'mythic' ? 'block' : 'none');
        document.querySelectorAll('.difficulty-heroic').forEach(el => el.style.display = diff === 'heroic' ? 'block' : 'none');
    }});
}});

function showChar(name) {{
    const modal = document.getElementById('modal');
    document.getElementById('modalTitle').textContent = name;
    
    if (details[name]) {{
        let content = details[name];
        let lines = content.split('\\n');
        let html = '';
        let inTable = false;
        let rows = [];
        let isEquipment = false;
        let isTrinket = false;
        
        for (let line of lines) {{
            if (line.startsWith('**SPEC_ICON:')) continue;
            
            if (line.includes('## ⚔️ Equipment')) isEquipment = true;
            else if (line.includes('## 🎯 Current Trinkets')) isTrinket = true;
            else if (line.startsWith('##')) {{ isEquipment = false; isTrinket = false; }}
            
            if (line.trim().startsWith('|')) {{
                if (!inTable) {{ inTable = true; rows = []; }}
                rows.push(line);
                continue;
            }} else if (inTable) {{
                html += processTable(rows, isEquipment, isTrinket);
                inTable = false;
                rows = [];
            }}
            
            if (line.startsWith('# ')) html += `<h2 style="color:#667eea;margin-top:30px">${{line.substring(2)}}</h2>`;
            else if (line.startsWith('## ')) html += `<h3 style="color:#764ba2;margin-top:25px;padding-bottom:10px;border-bottom:2px solid #e0e0e0">${{line.substring(3)}}</h3>`;
            else if (line.startsWith('### ')) html += `<h4 style="color:#667eea;margin-top:20px">${{line.substring(4)}}</h4>`;
            else if (line.trim() === '---') html += '<hr style="border:none;border-top:2px solid #e0e0e0;margin:20px 0">';
            else if (line.trim() === '') html += '<br>';
            else {{
                line = line.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>').replace(/\\*(.+?)\\*/g, '<em>$1</em>');
                html += `<p style="margin:10px 0;line-height:1.6">${{line}}</p>`;
            }}
        }}
        
        if (inTable) html += processTable(rows, isEquipment, isTrinket);
        
        document.getElementById('modalBody').innerHTML = html;
        modal.style.display = 'block';
    }}
}}

function processTable(rows, isEquipment, isTrinket) {{
    if (!rows.length) return '';
    
    let html = '<table style="width:100%;border-collapse:collapse;margin:20px 0;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 4px 10px rgba(0,0,0,0.1)">';
    
    for (let i = 0; i < rows.length; i++) {{
        const cells = rows[i].split('|').filter(c => c.trim());
        if (cells[0] && cells[0].includes('---')) continue;
        
        if (i === 0) {{
            html += '<thead><tr>';
            cells.forEach((c, idx) => {{
                if (!((isEquipment || isTrinket) && idx === 3 && c.trim() === 'Icon')) {{
                    html += `<th style="background:#667eea;color:#fff;padding:15px;text-align:left">${{c.trim()}}</th>`;
                }}
            }});
            html += '</tr></thead><tbody>';
        }} else {{
            html += '<tr>';
            cells.forEach((c, idx) => {{
                if (isEquipment || isTrinket) {{
                    if (idx === 0 && cells.length >= 4) {{
                        const iconCell = cells[3].trim();
                        let iconUrl = '';
                        if (iconCell.startsWith('ICON:')) iconUrl = iconCell.substring(5);
                        else if (iconCell.startsWith('TRINKET_ICON:')) iconUrl = iconCell.substring(13);
                        
                        if (iconUrl && iconUrl.startsWith('http')) {{
                            html += `<td style="padding:12px 15px"><img src="${{iconUrl}}" style="width:36px;height:36px;vertical-align:middle;margin-right:10px;border-radius:6px;border:2px solid #667eea" onerror="this.style.display='none'"> ${{c.trim()}}</td>`;
                        }} else {{
                            html += `<td style="padding:12px 15px">${{c.trim()}}</td>`;
                        }}
                    }} else if (idx === 2 && isEquipment) {{
                        const upgrade = c.trim();
                        let color = '#667eea';
                        if (upgrade.includes('8/8')) color = '#ff8000';
                        else if (upgrade.includes('7/8') || upgrade.includes('6/8')) color = '#a335ee';
                        else if (upgrade.includes('5/8') || upgrade.includes('4/8')) color = '#0070dd';
                        html += `<td style="padding:12px 15px"><span style="color:${{color}};font-weight:600">${{upgrade}}</span></td>`;
                    }} else if (idx !== 3) {{
                        html += `<td style="padding:12px 15px">${{c.trim()}}</td>`;
                    }}
                }} else {{
                    // For boss rankings table, show rank information properly
                    if (idx === 1 && c.trim().includes('%')) {{
                        // This is the rank percent column
                        html += `<td style="padding:12px 15px;font-weight:600">${{c.trim()}}</td>`;
                    }} else {{
                        html += `<td style="padding:12px 15px">${{c.trim()}}</td>`;
                    }}
                }}
            }});
            html += '</tr>';
        }}
    }}
    
    return html + '</tbody></table>';
}}

function closeModal() {{
    document.getElementById('modal').style.display = 'none';
}}

// Charts
const bgPlugin = {{
    beforeDraw: (chart) => {{
        const ctx = chart.ctx;
        ctx.save();
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, chart.width, chart.height);
        ctx.restore();
    }}
}};

new Chart(document.getElementById('trendChart'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(guild_history['dates'])},
        datasets: [
            {{ label: 'ilvl', data: {json.dumps(guild_history['avg_ilvl'])}, borderColor: '#667eea', backgroundColor: 'rgba(102,126,234,0.1)', tension: 0.4, fill: true, yAxisID: 'y1' }},
            {{ label: 'M+', data: {json.dumps(guild_history['avg_mplus'])}, borderColor: '#FF6B6B', backgroundColor: 'rgba(255,107,107,0.1)', tension: 0.4, fill: true, yAxisID: 'y2' }},
            {{ label: 'WCL', data: {json.dumps(guild_history['avg_wcl'])}, borderColor: '#4ECDC4', backgroundColor: 'rgba(78,205,196,0.1)', tension: 0.4, fill: true, yAxisID: 'y3' }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: true, position: 'top' }} }},
        scales: {{
            y1: {{ type: 'linear', position: 'left', title: {{ display: true, text: 'ilvl', color: '#667eea' }}, ticks: {{ color: '#667eea' }} }},
            y2: {{ type: 'linear', position: 'right', title: {{ display: true, text: 'M+', color: '#FF6B6B' }}, ticks: {{ color: '#FF6B6B' }}, grid: {{ display: false }} }},
            y3: {{ type: 'linear', position: 'right', title: {{ display: true, text: 'WCL', color: '#4ECDC4' }}, ticks: {{ color: '#4ECDC4' }}, grid: {{ display: false }} }}
        }}
    }},
    plugins: [bgPlugin]
}});

new Chart(document.getElementById('ilvlChart'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(names)}, datasets: [{{ label: 'ilvl', data: {json.dumps(ilvl_data)}, backgroundColor: {json.dumps(colors)}, borderColor: '#000', borderWidth: 2 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }}, y: {{ min: 720, max: 730, title: {{ display: true, text: 'Item Level' }} }} }} }},
    plugins: [bgPlugin]
}});

new Chart(document.getElementById('mplusChart'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(names)}, datasets: [{{ label: 'M+', data: {json.dumps(mplus_data_chart)}, backgroundColor: {json.dumps(colors)}, borderColor: '#000', borderWidth: 2 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }}, y: {{ title: {{ display: true, text: 'M+ Score' }} }} }} }},
    plugins: [bgPlugin]
}});

new Chart(document.getElementById('wclChart'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(wcl_filtered_names)}, datasets: [{{ label: 'WCL', data: {json.dumps(wcl_filtered_data)}, backgroundColor: {json.dumps(wcl_filtered_colors)}, borderColor: '#000', borderWidth: 2 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }}, y: {{ min: 0, max: 100, title: {{ display: true, text: 'WCL %' }} }} }} }},
    plugins: [bgPlugin]
}});
</script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Enhanced Dashboard v3 generated: {output_file}")
    print(f"   ✨ Features:")
    print(f"   - 🎯 Trinket tracking (current equipment)")
    print(f"   - 🛡️ 11 raid buffs with visual coverage")
    print(f"   - 🔗 Proper icons for Armory/RIO/WCL links")
    print(f"   - ✅ Fixed tab navigation")
    print(f"   - 📊 Boss rank details visible in modal")
    
    if missing_buffs:
        print(f"\n⚠️  Missing Raid Buffs:")
        for buff in missing_buffs:
            print(f"   - {buff['name']} (from {', '.join(buff['classes'])})")
    else:
        print(f"\n✅ All 11 raid buffs covered!")

if __name__ == "__main__":
    generate_html_dashboard("logs/Player_data.csv")
