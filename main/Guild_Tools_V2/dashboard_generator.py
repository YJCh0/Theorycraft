import csv
import os
import json
from datetime import datetime

# Complete Raid buff mapping - 13 essential buffs
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
    """Extract WCL data from markdown content"""
    wcl_data = {
        'has_logs': False,
        'best_performance': 'N/A',
        'boss_rankings': [],
        'all_stars': []
    }
    
    lines = content.split('\n')
    in_wcl_section = False
    in_boss_table = False
    in_allstars_table = False
    
    for i, line in enumerate(lines):
        if '## 🏆 WarcraftLogs Performance' in line:
            in_wcl_section = True
            # Check next line for "No raid logs"
            if i + 1 < len(lines) and 'No raid logs' in lines[i + 1]:
                return wcl_data
            wcl_data['has_logs'] = True
        
        if in_wcl_section:
            if 'Best Performance Average:' in line:
                try:
                    wcl_data['best_performance'] = line.split('**')[1].strip()
                except:
                    pass
            
            if '### 📋 Boss Rankings' in line:
                in_boss_table = True
                continue
            
            if '### ⭐ All Stars Points' in line:
                in_boss_table = False
                in_allstars_table = True
                continue
            
            if in_boss_table and line.startswith('|') and '---' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 4 and parts[0] not in ['Boss', '']:
                    try:
                        wcl_data['boss_rankings'].append({
                            'boss': parts[0],
                            'rank_percent': parts[1].replace('%', '').strip(),
                            'best_amount': int(parts[2].replace(',', '')),
                            'total_kills': int(parts[3])
                        })
                    except:
                        pass
            
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

def get_rio_color(score):
    """Get Raider.IO color based on score"""
    if score >= 3500: return '#ff8000'  # Orange
    elif score >= 3000: return '#a335ee'  # Epic Purple
    elif score >= 2500: return '#0070dd'  # Rare Blue
    elif score >= 2000: return '#1eff00'  # Uncommon Green
    elif score >= 1500: return '#ffffff'  # Common White
    else: return '#808080'  # Gray

def parse_wcl_from_markdown(content):
    """Extract WCL data from markdown content for both difficulties"""
    wcl_data = {
        'has_logs': False,
        'mythic': {
            'best_performance': 'N/A',
            'boss_rankings': []
        },
        'heroic': {
            'best_performance': 'N/A',
            'boss_rankings': []
        },
        'all_stars': []
    }
    
    lines = content.split('\n')
    current_difficulty = None
    in_boss_table = False
    in_allstars_table = False
    
    for i, line in enumerate(lines):
        # Check for Mythic section
        if '## 🏆 WarcraftLogs Performance - Mythic' in line:
            current_difficulty = 'mythic'
            wcl_data['has_logs'] = True
            continue
        
        # Check for Heroic section
        if '## 🏆 WarcraftLogs Performance - Heroic' in line:
            current_difficulty = 'heroic'
            wcl_data['has_logs'] = True
            continue
        
        # Check for All Stars (goes in main section)
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
                        wcl_data[current_difficulty]['boss_rankings'].append({
                            'boss': parts[0],
                            'rank_percent': parts[1].replace('%', '').strip(),
                            'best_amount': int(parts[2].replace(',', '')),
                            'total_kills': int(parts[3])
                        })
                    except:
                        pass
            
            # Stop boss table when we hit another section
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
    """Generate complete interactive dashboard with 5 tabs"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🎨 Generating enhanced dashboard...")
    
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
    
    # Read characters and their detailed data
    characters = []
    character_specs = {}
    character_details = {}
    wcl_details = {}
    character_servers = {}  # Initialize this early, before any other code    

    with open(csv_file, 'r', encoding='utf-8') as f:
        characters = list(csv.DictReader(f))
    
    if os.path.exists(detailed_dir):
        for fname in os.listdir(detailed_dir):
            if fname.endswith('.md'):
                name = fname[:-3]
                with open(os.path.join(detailed_dir, fname), 'r', encoding='utf-8') as f:
                    content = f.read()
                    character_details[name] = content
                    
                    # Extract spec icon
                    for line in content.split('\n'):
                        if line.startswith('**SPEC_ICON:'):
                            character_specs[name] = line.replace('**SPEC_ICON:', '').replace('**', '').strip()
                            break
                    
                    # Extract WCL data from markdown
                    wcl_details[name] = parse_wcl_from_markdown(content)
    
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
    wcl_data = [float(str(c['WCL']).replace(',','')) if c['WCL']!='N/A' else 0 for c in characters]
    
    classes = [c['Class'] for c in characters]
    class_colors = {
        'Deathknight':'#C41E3A','Demon Hunter':'#A330C9','Druid':'#FF7C0A',
        'Evoker':'#33937F','Hunter':'#AAD372','Mage':'#3FC7EB',
        'Monk':'#00FF98','Paladin':'#F48CBA','Priest':'#FFFFFF',
        'Rogue':'#FFF468','Shaman':'#0070DD','Warlock':'#8788EE',
        'Warrior':'#C69B6D','Demonhunter':'#A330C9'
    }
    colors = [class_colors.get(c,'#667eea') for c in classes]
    
    # Create filtered WCL data (only characters with actual scores)
    wcl_filtered_names = []
    wcl_filtered_data = []
    wcl_filtered_colors = []
    for c in characters:
        try:
            wcl_val = float(str(c['WCL']).replace(',',''))
            if wcl_val > 0:  # Only include characters with actual WCL data
                wcl_filtered_names.append(c['ID'])
                wcl_filtered_data.append(wcl_val)
                # Get class color for this character
                char_class = c['Class']
                char_color = class_colors.get(char_class, '#667eea')
                wcl_filtered_colors.append(char_color)
        except:
            pass
    
    print(f"   - WCL chart: {len(wcl_filtered_names)} characters with raid logs")
    print(f"   - WCL colors: {wcl_filtered_colors[:3]}...")  # Debug: print first 3 colors
    
    def wcl_color(s):
        if s==100: return '#e6cc80'
        elif s>=99: return '#e367a5'
        elif s>=95: return '#ff8000'
        elif s>=75: return '#a335ee'
        elif s>=50: return '#0070dd'
        elif s>=25: return '#1eff00'
        return '#808080'
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<title>Guild Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}}
.container{{max-width:1400px;margin:0 auto}}
header{{text-align:center;color:#fff;margin-bottom:40px;padding:20px}}
h1{{font-size:3em}}
h2{{font-size:1.8em;margin-bottom:20px}}
h3{{font-size:1.4em}}
@media(max-width:768px){{
body{{padding:10px}}
h1{{font-size:1.8em}}
h2{{font-size:1.3em;margin-bottom:15px}}
h3{{font-size:1.1em}}
header{{padding:10px;margin-bottom:20px}}
.stats-grid{{grid-template-columns:repeat(2,1fr)!important;gap:10px!important}}
.stat-card{{padding:15px!important}}
.stat-card h3{{font-size:0.9em}}
.value{{font-size:1.5em!important}}
.tab-nav{{flex-wrap:wrap}}
.tab-btn{{padding:12px 8px!important;font-size:0.85em!important;min-width:0}}
.tab-content{{padding:15px!important}}
.chart-container{{height:300px!important;padding:10px!important}}
.char-section{{padding:15px!important}}
.char-header{{flex-direction:column!important;align-items:flex-start!important}}
.char-avatar{{width:50px!important;height:50px!important;margin-bottom:10px!important;margin-right:0!important}}
.run-card{{padding:12px!important}}
.run-header{{flex-direction:column!important;align-items:flex-start!important;gap:10px}}
.key-level{{font-size:1.2em!important;padding:6px 12px!important}}
.sort-controls{{gap:6px!important}}
.sort-btn{{padding:8px 10px!important;font-size:0.8em!important}}
table{{font-size:0.85em}}
th,td{{padding:8px!important;font-size:0.85em}}
.modal-content{{width:95%!important;margin:20px auto!important;max-height:90vh!important}}
.modal-header{{padding:15px!important}}
.modal-body{{padding:15px!important}}
.roster{{grid-template-columns:1fr!important}}
.affixes{{gap:5px!important}}
.affix{{font-size:0.75em!important;padding:4px 8px!important}}
.badge{{font-size:0.75em!important;padding:3px 8px!important}}
.boss-card{{padding:15px!important}}
}}
@media(max-width:480px){{
h1{{font-size:1.5em}}
.stats-grid{{gap:8px!important}}
.stat-card{{padding:12px!important}}
.value{{font-size:1.3em!important}}
.tab-btn{{padding:10px 6px!important;font-size:0.75em!important}}
.tab-content{{padding:10px!important}}
table{{font-size:0.75em}}
th,td{{padding:6px!important}}
.chart-container{{height:250px!important}}
}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}}
.stat-card{{background:#fff;border-radius:15px;padding:25px;box-shadow:0 10px 30px rgba(0,0,0,.2)}}
.value{{font-size:2.5em;font-weight:bold;color:#667eea}}
.tab-container{{background:#fff;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.2);margin-bottom:40px;overflow:hidden}}
.tab-nav{{display:flex;background:#f0f0f0;border-bottom:2px solid #667eea}}
.tab-btn{{flex:1;padding:20px;background:none;border:none;cursor:pointer;font-size:1.1em;font-weight:600;color:#666;transition:all .3s}}
.tab-btn:hover{{background:rgba(102,126,234,.1)}}
.tab-btn.active{{background:#fff;color:#667eea;border-bottom:3px solid #667eea}}
.tab-content{{display:none;padding:30px;overflow-x:auto}}
.tab-content.active{{display:block}}
.chart-container{{position:relative;height:600px;padding:20px;background:#fff;border-radius:10px;border:2px solid #e0e0e0}}
.sort-controls{{display:flex;gap:15px;margin-bottom:20px;flex-wrap:wrap}}
.sort-btn{{padding:10px 20px;background:#f0f0f0;border:2px solid #667eea;border-radius:8px;cursor:pointer;font-weight:600;color:#667eea;transition:all .3s}}
.sort-btn:hover{{background:#667eea;color:#fff}}
.sort-btn.active{{background:#667eea;color:#fff}}
table{{width:100%;border-collapse:collapse}}
th{{background:#667eea;color:#fff;padding:12px;text-align:left;cursor:pointer;user-select:none}}
th:hover{{background:#764ba2}}
td{{padding:12px;border-bottom:1px solid #eee}}
tr:hover{{background:#f8f9ff}}
.clickable{{cursor:pointer;color:#667eea;font-weight:600;text-decoration:none}}
.clickable:hover{{text-decoration:underline}}
.badge{{display:inline-block;padding:4px 12px;border-radius:12px;font-size:.85em;font-weight:600}}
.modal{{display:none;position:fixed;z-index:1000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.6)}}
.modal-content{{background:#fff;margin:50px auto;padding:0;border-radius:15px;width:90%;max-width:900px;max-height:85vh;overflow-y:auto}}
.modal-header{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:25px;border-radius:15px 15px 0 0;position:sticky;top:0;z-index:1001}}
.modal-body{{padding:30px}}
.close{{color:#fff;float:right;font-size:32px;font-weight:bold;cursor:pointer}}
.char-section{{background:#f8f9fa;border-radius:15px;padding:25px;margin-bottom:30px;border:2px solid #e0e0e0}}
.char-header{{display:flex;align-items:center;margin-bottom:20px;padding-bottom:15px;border-bottom:2px solid #667eea}}
.char-avatar{{width:80px;height:80px;border-radius:10px;margin-right:20px;border:3px solid #667eea}}
.run-card{{background:#fff;border-radius:10px;padding:20px;margin-bottom:15px;border-left:4px solid #667eea}}
.run-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}}
.key-level{{font-size:1.8em;font-weight:bold;padding:10px 25px;border-radius:10px;color:#fff;box-shadow:0 4px 10px rgba(0,0,0,.2)}}
.upgrade-badge{{display:inline-block;margin-left:8px;font-size:0.8em;background:rgba(255,255,255,.3);padding:4px 10px;border-radius:6px}}
.affixes{{display:flex;gap:10px;margin:15px 0;flex-wrap:wrap}}
.affix{{background:#667eea;color:#fff;padding:6px 12px;border-radius:6px;font-size:.85em}}
.roster{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-top:15px}}
.roster-member{{background:#f8f9fa;padding:12px;border-radius:8px;display:flex;align-items:center;gap:12px;border:1px solid #e0e0e0}}
.role-icon{{width:35px;height:35px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.2em}}
.tank{{background:#C41E3A;color:#fff}}
.healer{{background:#1EFF00;color:#fff}}
.dps{{background:#667eea;color:#fff}}
.boss-card{{background:#f8f9fa;padding:20px;border-radius:10px;margin-bottom:15px;border-left:4px solid}}
.perf-bar{{height:30px;border-radius:6px;position:relative;overflow:hidden;margin-top:10px}}
.perf-fill{{height:100%;transition:width .5s;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600}}
footer{{text-align:center;color:#fff;margin-top:40px}}
</style>
</head>
<body>
<div class="container">
<header><h1>⚔️ Guild Dashboard</h1><p>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p></header>
<div class="stats-grid">
<div class="stat-card"><h3>Members</h3><div class="value">{total}</div></div>
<div class="stat-card"><h3>Avg ilvl</h3><div class="value">{avg_ilvl:.1f}</div></div>
<div class="stat-card"><h3>Avg M+</h3><div class="value">{avg_mplus:.1f}</div></div>
<div class="stat-card"><h3>Avg WCL</h3><div class="value">{avg_wcl:.1f}</div></div>
</div>
<div class="tab-container">
<div class="tab-nav">
<button class="tab-btn active" onclick="switchTab(event,'overview')">📊 Overview</button>
<button class="tab-btn" onclick="switchTab(event,'roster')">📋 Roster</button>
<button class="tab-btn" onclick="switchTab(event,'charts')">📈 Charts</button>
<button class="tab-btn" onclick="switchTab(event,'mplus')">🏔️ M+ Details</button>
<button class="tab-btn" onclick="switchTab(event,'raiding')">🏆 Raiding</button>
</div>
<div id="overview" class="tab-content active">
<h2>Guild Progress Trends</h2>
<div class="chart-container"><canvas id="trendChart"></canvas></div>
<h2 style="margin-top:40px">🏆 Top Improvers (Last 7 Days)</h2>
<table style="margin-top:20px"><thead><tr><th style="width:80px">Rank</th><th>Character</th><th>Class & Spec</th><th>ilvl</th><th>M+</th><th>WCL</th></tr></thead><tbody>
"""
    
    # Top Improvers
    if top_improvers:
        for i,p in enumerate(top_improvers[:10],1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            html_content += f'<tr><td>{medal}</td><td><b>{p["name"]}</b></td><td>{p["spec"]} {p["class"]}</td><td style="color:#28a745">+{p["ilvl_gain"]:.1f}</td><td style="color:#28a745">+{p["mplus_gain"]:.0f}</td><td style="color:#28a745">+{p["wcl_gain"]:.1f}</td></tr>'
    else:
        html_content += '<tr><td colspan="6" style="text-align:center;padding:20px">No data yet</td></tr>'
    
    # Roster Tab with sorting
    html_content += """</tbody></table></div>
<div id="roster" class="tab-content">
<h2>Character Roster</h2>
<div class="sort-controls">
<button class="sort-btn active" onclick="sortRoster('name')">📝 Name (A-Z)</button>
<button class="sort-btn" onclick="sortRoster('ilvl')">⚔️ Item Level</button>
<button class="sort-btn" onclick="sortRoster('mplus')">🏔️ M+ Score</button>
<button class="sort-btn" onclick="sortRoster('wcl')">📈 WCL Score</button>
</div>
<table id="rosterTable" style="margin-top:20px"><thead><tr><th onclick="sortRoster('name')">Character</th><th>Class</th><th>Spec</th><th onclick="sortRoster('ilvl')">ilvl</th><th onclick="sortRoster('mplus')">M+</th><th onclick="sortRoster('wcl')">WCL</th><th>Links</th></tr></thead><tbody>
"""
    
    # Store roster data in JSON for client-side sorting
    roster_data = []
    for c in characters:
        name = c['ID']
        has_detail = name in character_details
        spec_icon = character_specs.get(name,'')
        server = character_servers.get(name, 'azshara')
        
        # Generate profile links
        armory_url = f"https://worldofwarcraft.blizzard.com/ko-kr/character/kr/{server.lower()}/{name.lower()}"
        raiderio_url = f"https://raider.io/characters/kr/{server}/{name}"
        wcl_url = f"https://www.warcraftlogs.com/character/kr/{server.lower()}/{name}"
        
        links_html = f'<a href="{armory_url}" target="_blank" title="Armory" style="display:inline-block;padding:6px 10px;background:#0070dd;color:#fff;text-decoration:none;border-radius:4px;font-size:0.85em;margin-right:4px">🛡️</a><a href="{raiderio_url}" target="_blank" title="Raider.IO" style="display:inline-block;padding:6px 10px;background:#667eea;color:#fff;text-decoration:none;border-radius:4px;font-size:0.85em;margin-right:4px">🏔️</a><a href="{wcl_url}" target="_blank" title="Warcraft Logs" style="display:inline-block;padding:6px 10px;background:#ff8000;color:#fff;text-decoration:none;border-radius:4px;font-size:0.85em">📊</a>'
        
        try:
            mp = float(str(c['M+']).replace(',',''))
            mp_color = get_rio_color(mp)
            mp_badge = f'<span class="badge" style="background:{mp_color};color:#fff">{mp:.0f}</span>'
        except:
            mp = 0
            mp_badge = '<span class="badge" style="background:#808080;color:#fff">N/A</span>'
        
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
    
    # Initial display (alphabetical)
    roster_data.sort(key=lambda x: x['name'])
    
    for rd in roster_data:
        spec_disp = f'<img src="{rd["spec_icon"]}" style="width:24px;height:24px;vertical-align:middle;margin-right:6px;border-radius:4px" onerror="this.style.display=\'none\'"> {rd["spec"]}' if rd["spec_icon"] else rd["spec"]
        name_disp = f'<a href="#" class="clickable" onclick="showChar(\'{rd["name"]}\');return false">{rd["name"]}</a>' if rd["has_detail"] else f'<b>{rd["name"]}</b>'
        
        html_content += f'<tr><td>{name_disp}</td><td>{rd["class"]}</td><td>{spec_disp}</td><td>{rd["ilvl_display"]}</td><td>{rd["mplus_badge"]}</td><td>{rd["wcl_badge"]}</td><td>{rd["links"]}</td></tr>'
    
    # Charts Tab
    html_content += """</tbody></table></div>
<div id="charts" class="tab-content">
<h2>Item Level Distribution</h2><div class="chart-container"><canvas id="ilvlChart"></canvas></div>
<h2 style="margin-top:40px">M+ Score Distribution</h2><div class="chart-container"><canvas id="mplusChart"></canvas></div>
<h2 style="margin-top:40px">WCL Performance Distribution</h2><div class="chart-container"><canvas id="wclChart"></canvas></div>
</div>
<div id="mplus" class="tab-content">
"""
    
    # M+ Tab with enhanced display
    if mplus_data:
        html_content += '<h2 style="margin-bottom:30px">🏔️ Mythic+ Recent Runs</h2>'
        sorted_m = sorted([(n,d) for n,d in mplus_data.items() if d], key=lambda x:x[1].get("character",{}).get("score",0), reverse=True)
        
        for name,data in sorted_m:
            ci = data.get("character",{})
            runs = data.get("best_runs",[])
            if not runs: continue
            
            score = ci.get("score",0)
            score_color = get_rio_color(score)
            
            html_content += f'<div class="char-section"><div class="char-header"><img src="{ci.get("thumbnail","")}" class="char-avatar" onerror="this.style.display=\'none\'"><div><h3>{ci.get("name",name)}</h3><div style="display:flex;gap:15px;margin-top:10px"><span class="badge">{ci.get("spec","")} {ci.get("class","")}</span><span class="badge">ilvl {ci.get("ilvl",0)}</span><span class="badge" style="background:{score_color};color:#fff">M+ {score:.0f}</span></div></div></div>'
            
            for i,run in enumerate(runs,1):
                lv = run.get('level',0)
                timed = run.get('timed',False)
                chests = run.get('num_chests',0)
                lv_col = "#FF8000" if lv>=12 else "#A335EE" if lv>=10 else "#0070DD" if lv>=8 else "#1EFF00"
                
                # Unified key level display
                if timed and chests > 0:
                    key_display = f'+{lv} <span class="upgrade-badge">(+{chests})</span>'
                else:
                    key_display = f'+{lv}'
                
                def fmt(ms):
                    if ms<=0: return "N/A"
                    s=ms/1000
                    return f"{int(s//60)}:{int(s%60):02d}"
                
                html_content += f'<div class="run-card"><div class="run-header"><div><div style="font-size:1.3em;font-weight:600">#{i} {run.get("dungeon","")}</div><div style="color:#666;font-size:.9em">{run.get("completed_at","")}</div></div><div class="key-level" style="background:{lv_col}">{key_display}</div></div><div style="margin-bottom:10px;font-weight:600;color:{"#28a745" if timed else "#dc3545"}">{"✅ Timed" if timed else "❌ Depleted"} | Score: {run.get("score",0):.1f}</div><div class="affixes">'
                
                aff_emoji = {"Tyrannical":"👑","Fortified":"🛡️","Bolstering":"💪","Bursting":"💥","Raging":"😡","Sanguine":"🩸","Volcanic":"🌋","Explosive":"💣","Quaking":"🌊","Grievous":"⚔️","Necrotic":"☠️","Storming":"⛈️","Afflicted":"🤢","Incorporeal":"👻","Entangling":"🌿","Xal'atath's Bargain":"🔮","Xal'atath's Guile":"🔮"}
                
                for aff in run.get('affixes',[]):
                    html_content += f'<span class="affix">{aff_emoji.get(aff.get("name",""),"🔸")} {aff.get("name","")}</span>'
                
                html_content += f'</div><div style="display:flex;gap:20px;margin:15px 0"><span>⏱️ {fmt(run.get("clear_time_ms",0))}</span><span>🎯 {fmt(run.get("par_time_ms",0))}</span></div><h4 style="color:#667eea">Party Composition</h4><div class="roster">'
                
                for mem in run.get('roster',[]):
                    role = mem.get('role','dps').lower()
                    emoji = "🛡️" if role=="tank" else "💚" if role=="healer" else "⚔️"
                    html_content += f'<div class="roster-member"><div class="role-icon {role}">{emoji}</div><div><div style="font-weight:600">{mem.get("name","")}</div><div style="font-size:.85em;color:#666">{mem.get("spec","")} {mem.get("class","")}</div></div></div>'
                
                if run.get('url'):
                    html_content += f'<a href="{run["url"]}" target="_blank" style="display:inline-block;margin-top:15px;padding:10px 20px;background:#667eea;color:#fff;text-decoration:none;border-radius:8px;font-weight:600">📊 View on Raider.IO</a>'
                
                html_content += '</div></div>'
            
            html_content += '</div>'
    else:
        html_content += '<div style="text-align:center;padding:60px"><h2>No M+ Data</h2><p>Run python mplus_enhanced.py to fetch detailed dungeon data</p></div>'
    
    # Raiding Tab
    html_content += """</div>
<div id="raiding" class="tab-content">
<h2 style="margin-bottom:20px">🏆 Warcraft Logs Performance</h2>
<div class="sort-controls" style="margin-bottom:30px">
<button class="sort-btn active" onclick="switchDifficulty('mythic')">⚔️ Mythic</button>
<button class="sort-btn" onclick="switchDifficulty('heroic')">🛡️ Heroic</button>
</div>
"""
    
    if wcl_details:
        sorted_wcl = sorted([(name, data, next((c for c in characters if c['ID']==name), None)) 
                            for name, data in wcl_details.items() if data.get('has_logs')], 
                           key=lambda x: float(str(x[2]['WCL']).replace(',','')) if x[2] and x[2]['WCL']!='N/A' else 0, 
                           reverse=True)
        
        for name, wcl_data, char_info in sorted_wcl:
            if not char_info:
                continue
            
            spec_icon = character_specs.get(name, '')
            
            # Get server from character details or use default
            server = character_servers.get(name, 'azshara') if 'character_servers' in locals() else 'azshara'
            char_class = char_info['Class']
            
            # Generate profile links
            armory_url = f"https://worldofwarcraft.blizzard.com/ko-kr/character/kr/{server.lower()}/{name.lower()}"
            raiderio_url = f"https://raider.io/characters/kr/{server}/{name}"
            wcl_url = f"https://www.warcraftlogs.com/character/kr/{server.lower()}/{name}"
            
            # Mythic data
            mythic_data = wcl_data.get('mythic', {})
            mythic_perf = mythic_data.get('best_performance', 'N/A')
            mythic_bosses = mythic_data.get('boss_rankings', [])
            
            # Heroic data
            heroic_data = wcl_data.get('heroic', {})
            heroic_perf = heroic_data.get('best_performance', 'N/A')
            heroic_bosses = heroic_data.get('boss_rankings', [])
            
            # Use best available performance for color
            mythic_perf_color = '#808080'
            heroic_perf_color = '#808080'
            
            try:
                if mythic_perf != 'N/A':
                    mythic_score = float(str(mythic_perf).replace(',',''))
                    mythic_perf_color = wcl_color(mythic_score)
            except:
                pass
            
            try:
                if heroic_perf != 'N/A':
                    heroic_score = float(str(heroic_perf).replace(',',''))
                    heroic_perf_color = wcl_color(heroic_score)
            except:
                pass
            
            html_content += f'<div class="char-section"><div class="char-header">'
            if spec_icon:
                html_content += f'<img src="{spec_icon}" class="char-avatar" onerror="this.style.display=\'none\'">'
            html_content += f'<div style="flex:1"><h3>{name}</h3><div style="display:flex;gap:15px;margin-top:10px;flex-wrap:wrap"><span class="badge">{char_info["Spec"]} {char_class}</span><span class="badge" style="background:{mythic_perf_color};color:#fff">Mythic: {mythic_perf}</span><span class="badge" style="background:{heroic_perf_color};color:#fff">Heroic: {heroic_perf}</span></div></div>'
            
            # Profile links
            html_content += f'<div style="display:flex;gap:10px;margin-left:auto"><a href="{armory_url}" target="_blank" title="Armory" style="padding:8px 12px;background:#0070dd;color:#fff;text-decoration:none;border-radius:6px;font-size:0.9em">🛡️</a><a href="{raiderio_url}" target="_blank" title="Raider.IO" style="padding:8px 12px;background:#667eea;color:#fff;text-decoration:none;border-radius:6px;font-size:0.9em">🏔️</a><a href="{wcl_url}" target="_blank" title="Warcraft Logs" style="padding:8px 12px;background:#ff8000;color:#fff;text-decoration:none;border-radius:6px;font-size:0.9em">📊</a></div></div>'
            
            # MYTHIC Boss Rankings
            if mythic_bosses:
                html_content += '<div class="difficulty-mythic"><h4 style="margin-bottom:15px;color:#a335ee">⚔️ Mythic Boss Performance</h4>'
                for boss in mythic_bosses:
                    boss_name = boss.get('boss', 'Unknown')
                    rank_pct = boss.get('rank_percent', 0)
                    best_amount = boss.get('best_amount', 0)
                    kills = boss.get('total_kills', 0)
                    
                    try:
                        rank_val = float(rank_pct)
                        boss_color = wcl_color(rank_val)
                    except:
                        rank_val = 0
                        boss_color = '#808080'
                    
                    html_content += f'<div class="boss-card" style="border-left-color:{boss_color}"><div style="display:flex;justify-content:space-between;align-items:center"><div><strong>{boss_name}</strong><div style="color:#666;font-size:.9em;margin-top:5px">{kills} kills | Best: {best_amount:,}</div></div><div style="font-size:1.5em;font-weight:bold;color:{boss_color}">{rank_pct}%</div></div><div class="perf-bar" style="background:#e0e0e0"><div class="perf-fill" style="width:{rank_val}%;background:{boss_color}">{rank_pct}%</div></div></div>'
                html_content += '</div>'
            
            # HEROIC Boss Rankings
            if heroic_bosses:
                html_content += '<div class="difficulty-heroic" style="display:none"><h4 style="margin-bottom:15px;color:#0070dd">🛡️ Heroic Boss Performance</h4>'
                for boss in heroic_bosses:
                    boss_name = boss.get('boss', 'Unknown')
                    rank_pct = boss.get('rank_percent', 0)
                    best_amount = boss.get('best_amount', 0)
                    kills = boss.get('total_kills', 0)
                    
                    try:
                        rank_val = float(rank_pct)
                        boss_color = wcl_color(rank_val)
                    except:
                        rank_val = 0
                        boss_color = '#808080'
                    
                    html_content += f'<div class="boss-card" style="border-left-color:{boss_color}"><div style="display:flex;justify-content:space-between;align-items:center"><div><strong>{boss_name}</strong><div style="color:#666;font-size:.9em;margin-top:5px">{kills} kills | Best: {best_amount:,}</div></div><div style="font-size:1.5em;font-weight:bold;color:{boss_color}">{rank_pct}%</div></div><div class="perf-bar" style="background:#e0e0e0"><div class="perf-fill" style="width:{rank_val}%;background:{boss_color}">{rank_pct}%</div></div></div>'
                html_content += '</div>'
            
            # All-Stars Summary (show in both modes)
            all_stars = wcl_data.get('all_stars', [])
            if all_stars:
                html_content += '<h4 style="margin-top:25px;margin-bottom:15px">⭐ All-Stars Points</h4><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px">'
                for star in all_stars:
                    partition = star.get('partition', 'N/A')
                    spec = star.get('spec', 'Unknown')
                    points = star.get('points', 0)
                    possible = star.get('possible', 0)
                    rank_pct = star.get('rank_percent', 0)
                    
                    try:
                        pct_val = (points / possible * 100) if possible > 0 else 0
                        star_color = wcl_color(rank_pct)
                    except:
                        pct_val = 0
                        star_color = '#808080'
                    
                    html_content += f'<div style="background:#f8f9fa;padding:15px;border-radius:10px;border:2px solid {star_color}"><div style="font-weight:600;margin-bottom:10px">{spec} - {partition}</div><div style="font-size:1.3em;color:{star_color};font-weight:bold">{points:.1f} / {possible:.1f}</div><div style="color:#666;font-size:.9em;margin-top:5px">Rank: {rank_pct}%</div></div>'
                
                html_content += '</div>'
            
            html_content += '</div>'
        
        if not sorted_wcl:
            html_content += '<div style="text-align:center;padding:60px"><h2>No Raid Logs Available</h2><p>Characters need raid parses on Warcraft Logs</p></div>'
    else:
        html_content += '<div style="text-align:center;padding:60px"><h2>No Raid Data</h2><p>Run the crawler to fetch Warcraft Logs data</p></div>'
    
    html_content += f"""</div>
</div>
<div id="modal" class="modal">
<div class="modal-content">
<div class="modal-header"><span class="close" onclick="closeModal()">&times;</span><h2 id="modalTitle">Details</h2></div>
<div class="modal-body" id="modalBody"></div>
</div>
</div>
<footer><p>두부킴의 유기견들</p></footer>
</div>
<script>
const details={json.dumps(character_details)};
const rosterData={json.dumps(roster_data)};
let currentSort='name';
let currentDifficulty='mythic';

function switchDifficulty(diff){{
    currentDifficulty=diff;
    document.querySelectorAll('.sort-controls .sort-btn').forEach(b=>b.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('.difficulty-mythic').forEach(el=>el.style.display=diff==='mythic'?'block':'none');
    document.querySelectorAll('.difficulty-heroic').forEach(el=>el.style.display=diff==='heroic'?'block':'none');
}}

function sortRoster(by){{
    currentSort=by;
    document.querySelectorAll('.sort-controls .sort-btn').forEach(b=>b.classList.remove('active'));
    event.target.classList.add('active');
    
    let sorted=[...rosterData];
    if(by==='name')sorted.sort((a,b)=>a.name.localeCompare(b.name));
    else if(by==='ilvl')sorted.sort((a,b)=>b.ilvl-a.ilvl);
    else if(by==='mplus')sorted.sort((a,b)=>b.mplus-a.mplus);
    else if(by==='wcl')sorted.sort((a,b)=>b.wcl-a.wcl);
    
    const tbody=document.querySelector('#rosterTable tbody');
    tbody.innerHTML='';
    sorted.forEach(rd=>{{
        const specDisp=rd.spec_icon?`<img src="${{rd.spec_icon}}" style="width:24px;height:24px;vertical-align:middle;margin-right:6px;border-radius:4px" onerror="this.style.display='none'"> ${{rd.spec}}`:rd.spec;
        const nameDisp=rd.has_detail?`<a href="#" class="clickable" onclick="showChar('${{rd.name}}');return false">${{rd.name}}</a>`:`<b>${{rd.name}}</b>`;
        tbody.innerHTML+=`<tr><td>${{nameDisp}}</td><td>${{rd.class}}</td><td>${{specDisp}}</td><td>${{rd.ilvl_display}}</td><td>${{rd.mplus_badge}}</td><td>${{rd.wcl_badge}}</td><td>${{rd.links}}</td></tr>`;
    }});
}}

function switchTab(e,t){{document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));document.querySelectorAll('.tab-btn').forEach(el=>el.classList.remove('active'));document.getElementById(t).classList.add('active');e.currentTarget.classList.add('active')}}

function showChar(n){{const m=document.getElementById('modal');document.getElementById('modalTitle').textContent=n;if(details[n]){{let c=details[n],lines=c.split('\\n'),html='',inT=false,rows=[],isEq=false,specIcon='';for(let line of lines){{if(line.startsWith('**SPEC_ICON:')){{specIcon=line.replace('**SPEC_ICON:','').replace('**','').trim();continue}}if(line.includes('## ⚔️ Equipment'))isEq=true;else if(line.startsWith('##'))isEq=false;if(line.trim().startsWith('|')){{if(!inT){{inT=true;rows=[]}}rows.push(line);continue}}else if(inT){{html+=procTable(rows,isEq);inT=false;rows=[]}}if(line.startsWith('# '))html+=`<h2>${{line.substring(2)}}</h2>`;else if(line.startsWith('## '))html+=`<h3>${{line.substring(3)}}</h3>`;else if(line.startsWith('### '))html+=`<h4>${{line.substring(4)}}</h4>`;else if(line.trim()==='---')html+='<hr>';else if(line.trim()==='')html+='<br>';else{{line=line.replace(/\\*\\*(.+?)\\*\\*/g,'<strong>$1</strong>').replace(/\\*(.+?)\\*/g,'<em>$1</em>');if(specIcon&&line.includes('|')&&(line.includes('Tank')||line.includes('Healer')||line.includes('Melee')||line.includes('Ranged')))line=`<img src="${{specIcon}}" style="width:24px;height:24px;vertical-align:middle;margin-right:8px;border-radius:4px;border:2px solid #667eea" onerror="this.style.display='none'"> `+line;html+=`<p>${{line}}</p>`}}}}if(inT)html+=procTable(rows,isEq);document.getElementById('modalBody').innerHTML=html;m.style.display='block'}}}}

function procTable(rows,isEq){{if(!rows.length)return '';let h='<table style="width:100%;border-collapse:collapse;margin:20px 0">';for(let i=0;i<rows.length;i++){{const cells=rows[i].split('|').filter(c=>c.trim());if(cells[0]&&cells[0].includes('---'))continue;if(i===0){{h+='<thead><tr>';cells.forEach((c,idx)=>{{if(!(isEq&&idx===4&&c.trim()==='Icon'))h+=`<th style="background:#667eea;color:#fff;padding:12px">${{c.trim()}}</th>`}});h+='</tr></thead><tbody>'}}else{{h+='<tr>';cells.forEach((c,idx)=>{{if(isEq){{if(idx===1&&cells.length>=5){{const ic=cells[4].trim();if(ic.startsWith('ICON:')){{const url=ic.substring(5);if(url&&url.startsWith('http'))h+=`<td style="padding:12px"><img src="${{url}}" style="width:32px;height:32px;vertical-align:middle;margin-right:8px;border-radius:4px;border:2px solid #667eea" onerror="this.style.display='none'"> ${{c.trim()}}</td>`;else h+=`<td style="padding:12px">${{c.trim()}}</td>`}}else h+=`<td style="padding:12px">${{c.trim()}}</td>`}}else if(idx===3){{const upgrade=c.trim();let color='#667eea';if(upgrade.includes('8/8'))color='#ff8000';else if(upgrade.includes('7/8')||upgrade.includes('6/8'))color='#a335ee';else if(upgrade.includes('5/8')||upgrade.includes('4/8'))color='#0070dd';else if(upgrade.includes('1/8')||upgrade.includes('2/8')||upgrade.includes('3/8'))color='#1eff00';h+=`<td style="padding:12px"><span style="color:${{color}};font-weight:600">${{upgrade}}</span></td>`}}else if(idx!==4)h+=`<td style="padding:12px">${{c.trim()}}</td>`}}else h+=`<td style="padding:12px">${{c.trim()}}</td>`}});h+='</tr>'}}}}return h+'</tbody></table>'}}

function closeModal(){{document.getElementById('modal').style.display='none'}}
window.onclick=e=>{{if(e.target==document.getElementById('modal'))closeModal()}}

const bg={{beforeDraw:c=>{{const x=c.ctx;x.save();x.fillStyle='#f8f9fa';x.fillRect(0,0,c.width,c.height);x.restore()}}}};

new Chart(document.getElementById('trendChart'),{{type:'line',data:{{labels:{json.dumps(guild_history['dates'])},datasets:[{{label:'ilvl',data:{json.dumps(guild_history['avg_ilvl'])},borderColor:'#667eea',tension:.4,yAxisID:'y1'}},{{label:'M+',data:{json.dumps(guild_history['avg_mplus'])},borderColor:'#FF6B6B',tension:.4,yAxisID:'y2'}},{{label:'WCL',data:{json.dumps(guild_history['avg_wcl'])},borderColor:'#4ECDC4',tension:.4,yAxisID:'y3'}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true,position:'top'}}}},scales:{{y1:{{type:'linear',position:'left',title:{{display:true,text:'ilvl',color:'#667eea'}},ticks:{{color:'#667eea'}}}},y2:{{type:'linear',position:'right',title:{{display:true,text:'M+',color:'#FF6B6B'}},ticks:{{color:'#FF6B6B'}},grid:{{display:false}}}},y3:{{type:'linear',position:'right',title:{{display:true,text:'WCL',color:'#4ECDC4'}},ticks:{{color:'#4ECDC4'}},grid:{{display:false}}}}}}}},plugins:[bg]}});

new Chart(document.getElementById('ilvlChart'),{{type:'bar',data:{{labels:{json.dumps(names)},datasets:[{{label:'Item Level',data:{json.dumps(ilvl_data)},backgroundColor:{json.dumps(colors)},borderColor:'#000000',borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true}}}},scales:{{x:{{ticks:{{autoSkip:false,maxRotation:0,minRotation:0}}}},y:{{min:720,max:730,title:{{display:true,text:'Item Level'}}}}}}}},plugins:[bg]}});

new Chart(document.getElementById('mplusChart'),{{type:'bar',data:{{labels:{json.dumps(names)},datasets:[{{label:'M+ Score',data:{json.dumps(mplus_data_chart)},backgroundColor:{json.dumps(colors)},borderColor:'#000000',borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true}}}},scales:{{x:{{ticks:{{autoSkip:false,maxRotation:0,minRotation:0}}}},y:{{title:{{display:true,text:'M+ Score'}}}}}}}},plugins:[bg]}});

const wclNames={json.dumps(wcl_filtered_names)};
const wclData={json.dumps(wcl_filtered_data)};
const wclColors={json.dumps(wcl_filtered_colors)};

console.log('WCL Names:', wclNames);
console.log('WCL Data:', wclData);
console.log('WCL Colors:', wclColors);

new Chart(document.getElementById('wclChart'),{{type:'bar',data:{{labels:wclNames,datasets:[{{label:'WCL Performance',data:wclData,backgroundColor:wclColors,borderColor:'#000000',borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true,position:'top'}}}},scales:{{x:{{ticks:{{autoSkip:false,maxRotation:0,minRotation:0}}}},y:{{min:0,max:100,title:{{display:true,text:'WCL Percentile'}}}}}}}},plugins:[bg]}});
</script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"   - 5 tabs (Overview, Roster, Charts, M+ Details, Raiding)")
    print(f"   - Roster with sortable columns (Name/ilvl/M+/WCL)")
    print(f"   - M+ scores colored by Raider.IO standard")

if __name__ == "__main__":
    generate_html_dashboard("logs/Player_data.csv")
