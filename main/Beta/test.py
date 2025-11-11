"""
Guild Dashboard Generator - Modular Version
Broken into smaller, maintainable functions
See dashboard_docs artifact for detailed documentation
"""

import csv
import os
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

RAID_BUFFS = {
    'battle_shout': {'name': 'Battle Shout', 'classes': ['Warrior'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_warrior_battleshout.jpg'},
    'mark_of_the_wild': {'name': 'Mark of the Wild', 'classes': ['Druid'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_nature_regeneration.jpg'},
    'arcane_intellect': {'name': 'Arcane Intellect', 'classes': ['Mage'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_holy_magicalsentry.jpg'},
    'skyfury': {'name': 'Skyfury', 'classes': ['Shaman'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/achievement_raidprimalist_windelemental.jpg'},
    'blessing_of_the_bronze': {'name': 'Blessing of the Bronze', 'classes': ['Evoker'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_evoker_blessingofthebronze.jpg'},
    'hunters_mark': {'name': "Hunter's Mark", 'classes': ['Hunter'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_hunter_markedfordeath.jpg'},
    'power_word_fortitude': {'name': 'Power Word: Fortitude', 'classes': ['Priest'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_holy_wordfortitude.jpg'},
    'devotion_aura': {'name': 'Devotion Aura', 'classes': ['Paladin'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_holy_devotionaura.jpg'},
    'numbing_poison': {'name': 'Numbing Poison', 'classes': ['Rogue'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_rogue_numbingpoison.jpg'},
    'mystic_touch': {'name': 'Mystic Touch', 'classes': ['Monk'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_monk_sparring.jpg'},
    'chaos_brand': {'name': 'Chaos Brand', 'classes': ['Demon Hunter', 'Demonhunter'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/ability_demonhunter_empowerwards.jpg'},
    'healthstone': {'name': 'Healthstone', 'classes': ['Warlock'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/warlock_-healthstone.jpg'},
    'death_grip': {'name': 'Death Grip', 'classes': ['Deathknight', 'Death Knight'], 'icon': 'https://wow.zamimg.com/images/wow/icons/large/spell_deathknight_strangulate.jpg'}
}

CLASS_COLORS = {
    'Deathknight': '#C41E3A', 'Demon Hunter': '#A330C9', 'Druid': '#FF7C0A',
    'Evoker': '#33937F', 'Hunter': '#AAD372', 'Mage': '#3FC7EB',
    'Monk': '#00FF98', 'Paladin': '#F48CBA', 'Priest': '#FFFFFF',
    'Rogue': '#FFF468', 'Shaman': '#0070DD', 'Warlock': '#8788EE',
    'Warrior': '#C69B6D', 'Demonhunter': '#A330C9'
}

# ============================================================================
# DATA PARSERS
# ============================================================================

def parse_wcl_from_markdown(content):
    """Extract WCL performance data from markdown content"""
    wcl_data = {
        'has_logs': False,
        'mythic': {'best_performance': 'N/A', 'boss_rankings': []},
        'heroic': {'best_performance': 'N/A', 'boss_rankings': []},
        'all_stars': []
    }
    
    lines = content.split('\n')
    current_difficulty = None
    in_boss_table = False
    
    for line in lines:
        if '## 🏆 WarcraftLogs Performance - Mythic' in line:
            current_difficulty = 'mythic'
            wcl_data['has_logs'] = True
        elif '## 🏆 WarcraftLogs Performance - Heroic' in line:
            current_difficulty = 'heroic'
            wcl_data['has_logs'] = True
        elif '### 📋 Boss Rankings' in line:
            in_boss_table = True
        elif in_boss_table and line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4 and parts[0] not in ['Boss', '']:
                try:
                    boss_entry = {
                        'boss': parts[0],
                        'rank_percent': parts[1].replace('%', '').strip(),
                        'best_amount': int(parts[2].replace(',', '')),
                        'total_kills': int(parts[3])
                    }
                    
                    if len(parts) >= 9:
                        boss_entry['rank_details'] = {
                            'partition': parts[4],
                            'spec': parts[5],
                            'overall': parts[6],
                            'region': parts[7],
                            'server': parts[8]
                        }
                    
                    if current_difficulty:
                        wcl_data[current_difficulty]['boss_rankings'].append(boss_entry)
                except:
                    pass
    
    return wcl_data

def parse_trinkets_from_markdown(content):
    """Extract trinket information from markdown"""
    trinkets = []
    lines = content.split('\n')
    in_trinket_section = False
    
    for line in lines:
        if '## 🎯 Current Trinkets' in line:
            in_trinket_section = True
        elif in_trinket_section and line.startswith('##'):
            break
        elif in_trinket_section and line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4 and parts[0] not in ['Trinket', '']:
                icon_url = ''
                if parts[3].startswith('TRINKET_ICON:'):
                    icon_url = parts[3].replace('TRINKET_ICON:', '').strip()
                
                trinkets.append({
                    'name': parts[0],
                    'ilvl': parts[1],
                    'upgrade': parts[2],
                    'icon': icon_url
                })
    
    return trinkets

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_rio_color(score):
    """Return color based on Raider.IO score"""
    if score >= 3500: return '#ff8000'
    elif score >= 3000: return '#a335ee'
    elif score >= 2500: return '#0070dd'
    elif score >= 2000: return '#1eff00'
    elif score >= 1500: return '#ffffff'
    else: return '#808080'

def wcl_color(score):
    """Return color based on WCL percentile"""
    if score == 100: return '#e6cc80'
    elif score >= 99: return '#e367a5'
    elif score >= 95: return '#ff8000'
    elif score >= 75: return '#a335ee'
    elif score >= 50: return '#0070dd'
    elif score >= 25: return '#1eff00'
    return '#808080'

def check_missing_buffs(characters):
    """Check which raid buffs are present/missing"""
    present_classes = {c['Class'].strip() for c in characters}
    missing_buffs = []
    present_buffs = []
    
    for buff_info in RAID_BUFFS.values():
        buff_classes = set(buff_info['classes'])
        if buff_classes.isdisjoint(present_classes):
            missing_buffs.append(buff_info)
        else:
            present_buffs.append(buff_info)
    
    return present_buffs, missing_buffs

# ============================================================================
# DATA LOADING
# ============================================================================

def load_character_data(csv_file, detailed_dir):
    """Load all character data from CSV and markdown files"""
    characters = []
    character_specs = {}
    character_details = {}
    wcl_details = {}
    character_servers = {}
    character_trinkets = {}
    
    # Read CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        characters = list(csv.DictReader(f))
    
    # Parse detailed markdown files
    if os.path.exists(detailed_dir):
        for fname in os.listdir(detailed_dir):
            if fname.endswith('.md'):
                name = fname[:-3]
                filepath = os.path.join(detailed_dir, fname)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    character_details[name] = content
                    
                    # Extract metadata
                    for line in content.split('\n'):
                        if line.startswith('**SPEC_ICON:'):
                            character_specs[name] = line.replace('**SPEC_ICON:', '').replace('**', '').strip()
                        if '|' in line and '**' in line:
                            parts = line.split('|')
                            if len(parts) >= 4:
                                server_part = parts[-2].strip()
                                if server_part.startswith('**') and server_part.endswith('**'):
                                    character_servers[name] = server_part.replace('**', '').strip()
                    
                    # Parse WCL and trinkets
                    wcl_details[name] = parse_wcl_from_markdown(content)
                    character_trinkets[name] = parse_trinkets_from_markdown(content)
    
    return {
        'characters': characters,
        'specs': character_specs,
        'details': character_details,
        'wcl': wcl_details,
        'servers': character_servers,
        'trinkets': character_trinkets
    }

def load_mplus_data():
    """Load M+ data from JSON file"""
    if os.path.exists("logs/mplus_enhanced.json"):
        with open("logs/mplus_enhanced.json", 'r') as f:
            return json.load(f)
    return {}

def load_history_data():
    """Load guild history data"""
    try:
        from history_tracker import get_guild_average_history, get_top_improvers
        return {
            'history': get_guild_average_history(),
            'improvers': get_top_improvers(7)
        }
    except:
        return {
            'history': {'dates': [], 'avg_ilvl': [], 'avg_mplus': [], 'avg_wcl': []},
            'improvers': []
        }

# ============================================================================
# HTML GENERATION - COMPONENTS
# ============================================================================

def generate_css():
    """Generate CSS styles for dashboard"""
    return """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}
.container{max-width:1400px;margin:0 auto}
header{text-align:center;color:#fff;margin-bottom:40px;padding:20px}
h1{font-size:3em;text-shadow:2px 2px 4px rgba(0,0,0,0.3)}
h2{font-size:1.8em;margin-bottom:20px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}
.stat-card{background:#fff;border-radius:15px;padding:25px;box-shadow:0 10px 30px rgba(0,0,0,.2);transition:transform .3s}
.stat-card:hover{transform:translateY(-5px)}
.value{font-size:2.5em;font-weight:bold;color:#667eea}
.tab-container{background:#fff;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.2);margin-bottom:40px;overflow:hidden}
.tab-nav{display:flex;background:#f0f0f0;border-bottom:2px solid #667eea}
.tab-btn{flex:1;padding:20px;background:none;border:none;cursor:pointer;font-size:1.1em;font-weight:600;color:#666;transition:all .3s;position:relative}
.tab-btn:hover{background:rgba(102,126,234,.1)}
.tab-btn.active{background:#fff;color:#667eea}
.tab-btn.active::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:#667eea}
.tab-content{display:none;padding:30px}
.tab-content.active{display:block}
.sort-controls{display:flex;gap:15px;margin-bottom:20px;flex-wrap:wrap}
.sort-btn{padding:10px 20px;background:#f0f0f0;border:2px solid #667eea;border-radius:8px;cursor:pointer;font-weight:600;color:#667eea;transition:all .3s}
.sort-btn:hover{background:#667eea;color:#fff}
.sort-btn.active{background:#667eea;color:#fff}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}
th{background:#667eea;color:#fff;padding:15px;text-align:left;font-weight:600}
td{padding:12px 15px;border-bottom:1px solid #eee}
tr:hover{background:#f8f9ff}
.profile-link{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;margin:0 2px;border-radius:6px;transition:all .3s;text-decoration:none}
.profile-link img{width:18px;height:18px}
.profile-link:hover{transform:translateY(-2px);box-shadow:0 4px 8px rgba(0,0,0,0.2)}
.armory-link{background:#0070dd}
.raiderio-link{background:#667eea}
.wcl-link{background:#ff8000}
.clickable{cursor:pointer;color:#667eea;font-weight:600;text-decoration:none;transition:color .3s}
.clickable:hover{color:#764ba2;text-decoration:underline}
.badge{display:inline-block;padding:5px 12px;border-radius:12px;font-size:.85em;font-weight:600;white-space:nowrap}
.modal{display:none;position:fixed;z-index:1000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.7)}
.modal-content{background:#fff;margin:30px auto;padding:0;border-radius:15px;width:95%;max-width:1200px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.modal-header{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:25px 30px;position:sticky;top:0;z-index:1001;display:flex;justify-content:space-between;align-items:center}
.modal-body{padding:30px}
.close{color:#fff;font-size:32px;font-weight:bold;cursor:pointer;transition:transform .3s}
.close:hover{transform:scale(1.1)}
.chart-container{position:relative;height:600px;padding:20px;background:#fff;border-radius:10px;border:2px solid #e0e0e0}
footer{text-align:center;color:#fff;margin-top:40px;padding:20px}
"""

def generate_header_html(stats):
    """Generate header and stats cards"""
    return f"""
<header>
<h1>⚔️ Guild Dashboard</h1>
<p style="font-size:1.2em;margin-top:10px">{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</header>

<div class="stats-grid">
<div class="stat-card"><h3>👥 Total Members</h3><div class="value">{stats['total']}</div></div>
<div class="stat-card"><h3>⚔️ Average ilvl</h3><div class="value">{stats['avg_ilvl']:.1f}</div></div>
<div class="stat-card"><h3>🏔️ Average M+</h3><div class="value">{stats['avg_mplus']:.1f}</div></div>
<div class="stat-card"><h3>📈 Average WCL</h3><div class="value">{stats['avg_wcl']:.1f}</div></div>
</div>
"""

def generate_roster_table_html(characters, char_data):
    """Generate roster table HTML"""
    rows = []
    for c in characters:
        name = c['ID']
        spec_icon = char_data['specs'].get(name, '')
        server = char_data['servers'].get(name, 'azshara')
        has_detail = name in char_data['details']
        
        # Profile links
        armory_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23fff'%3E%3Cpath d='M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z'/%3E%3C/svg%3E"
        rio_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23fff'%3E%3Cpath d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/%3E%3C/svg%3E"
        wcl_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23fff'%3E%3Cpath d='M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z'/%3E%3C/svg%3E"
        
        armory_url = f"https://worldofwarcraft.blizzard.com/ko-kr/character/kr/{server.lower()}/{name.lower()}"
        raiderio_url = f"https://raider.io/characters/kr/{server}/{name}"
        wcl_url = f"https://www.warcraftlogs.com/character/kr/{server.lower()}/{name}"
        
        links = f'<a href="{armory_url}" target="_blank" class="profile-link armory-link"><img src="{armory_svg}" alt="Armory"></a>'
        links += f'<a href="{raiderio_url}" target="_blank" class="profile-link raiderio-link"><img src="{rio_svg}" alt="RIO"></a>'
        links += f'<a href="{wcl_url}" target="_blank" class="profile-link wcl-link"><img src="{wcl_svg}" alt="WCL"></a>'
        
        # Badges
        try:
            mp = float(str(c['M+']).replace(',', ''))
            mp_color = get_rio_color(mp)
            mp_badge = f'<span class="badge" style="background:{mp_color};color:#fff">{mp:.0f}</span>'
        except:
            mp_badge = '<span class="badge" style="background:#808080;color:#fff">N/A</span>'
        
        try:
            wc = float(str(c['WCL']).replace(',', ''))
            wc_color = wcl_color(wc)
            wc_badge = f'<span class="badge" style="background:{wc_color};color:#fff">{wc:.1f}</span>'
        except:
            wc_badge = '<span class="badge" style="background:#808080;color:#fff">N/A</span>'
        
        # Name cell
        if has_detail:
            name_cell = f'<a href="#" class="clickable" onclick="showChar(\'{name}\');return false">{name}</a>'
        else:
            name_cell = f'<b>{name}</b>'
        
        # Spec cell
        if spec_icon:
            spec_cell = f'<img src="{spec_icon}" style="width:28px;height:28px;vertical-align:middle;margin-right:8px;border-radius:4px;border:2px solid #667eea" onerror="this.style.display=\'none\'"> {c["Spec"]}'
        else:
            spec_cell = c['Spec']
        
        rows.append(f'<tr><td>{name_cell}</td><td>{c["Class"]}</td><td>{spec_cell}</td><td><b>{c["ilvl"]}</b></td><td>{mp_badge}</td><td>{wc_badge}</td><td>{links}</td></tr>')
    
    return '\n'.join(rows)

def generate_javascript(char_data, chart_data):
    """Generate JavaScript for interactivity"""
    return f"""
<script>
const details = {json.dumps(char_data['details'])};
const wclData = {json.dumps({name: {'mythic': data.get('mythic', {}), 'heroic': data.get('heroic', {}), 'trinkets': char_data['trinkets'].get(name, [])} for name, data in char_data['wcl'].items()})};

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', function() {{
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        document.getElementById(this.dataset.tab).classList.add('active');
    }});
}});

// Modal
function showChar(name) {{
    document.getElementById('modalTitle').textContent = name;
    let html = '<h3>Character: ' + name + '</h3>';
    if (details[name]) {{
        html += '<pre style="white-space:pre-wrap;font-family:inherit">' + details[name].substring(0, 2000) + '</pre>';
    }}
    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('modal').style.display = 'block';
}}

function closeModal() {{
    document.getElementById('modal').style.display = 'none';
}}

// Charts
new Chart(document.getElementById('ilvlChart'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(chart_data['names'])},
        datasets: [{{
            label: 'ilvl',
            data: {json.dumps(chart_data['ilvl_data'])},
            backgroundColor: {json.dumps(chart_data['colors'])}
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false
    }}
}});

new Chart(document.getElementById('mplusChart'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(chart_data['names'])},
        datasets: [{{
            label: 'M+',
            data: {json.dumps(chart_data['mplus_data'])},
            backgroundColor: {json.dumps(chart_data['colors'])}
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false
    }}
}});
</script>
"""

# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_html_dashboard(csv_file, output_file="dashboard.html", detailed_dir="detailed"):
    """Main function to generate dashboard"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🎨 Generating dashboard...")
    
    # Load all data
    char_data = load_character_data(csv_file, detailed_dir)
    mplus_data = load_mplus_data()
    history_data = load_history_data()
    
    characters = char_data['characters']
    
    # Calculate stats
    total = len(characters)
    ilvls = [float(c['ilvl']) for c in characters if c['ilvl'] != 'N/A']
    mplus_scores = [float(str(c['M+']).replace(',', '')) for c in characters if c['M+'] != 'N/A']
    wcl_scores = [float(str(c['WCL']).replace(',', '')) for c in characters if c['WCL'] != 'N/A']
    
    stats = {
        'total': total,
        'avg_ilvl': sum(ilvls) / len(ilvls) if ilvls else 0,
        'avg_mplus': sum(mplus_scores) / len(mplus_scores) if mplus_scores else 0,
        'avg_wcl': sum(wcl_scores) / len(wcl_scores) if wcl_scores else 0
    }
    
    # Prepare chart data
    names = [c['ID'] for c in characters]
    ilvl_data = [float(c['ilvl']) if c['ilvl'] != 'N/A' else 0 for c in characters]
    mplus_data_chart = [float(str(c['M+']).replace(',', '')) if c['M+'] != 'N/A' else 0 for c in characters]
    colors = [CLASS_COLORS.get(c['Class'], '#667eea') for c in characters]
    
    chart_data = {
        'names': names,
        'ilvl_data': ilvl_data,
        'mplus_data': mplus_data_chart,
        'colors': colors
    }
    
    # Generate HTML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guild Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
{generate_css()}
</style>
</head>
<body>
<div class="container">
{generate_header_html(stats)}

<div class="tab-container">
<div class="tab-nav">
<button class="tab-btn active" data-tab="overview">📊 Overview</button>
<button class="tab-btn" data-tab="roster">📋 Roster</button>
<button class="tab-btn" data-tab="charts">📈 Charts</button>
</div>

<div id="overview" class="tab-content active">
<h2>Guild Overview</h2>
<p>Total members: {total}</p>
</div>

<div id="roster" class="tab-content">
<h2>Character Roster</h2>
<table id="rosterTable">
<thead>
<tr><th>Character</th><th>Class</th><th>Spec</th><th>ilvl</th><th>M+</th><th>WCL</th><th>Links</th></tr>
</thead>
<tbody>
{generate_roster_table_html(characters, char_data)}
</tbody>
</table>
</div>

<div id="charts" class="tab-content">
<h2>📊 Item Level Distribution</h2>
<div class="chart-container"><canvas id="ilvlChart"></canvas></div>
<h2 style="margin-top:40px">🏔️ M+ Score Distribution</h2>
<div class="chart-container"><canvas id="mplusChart"></canvas></div>
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

{generate_javascript(char_data, chart_data)}
</body>
</html>""")
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"   📊 {total} characters processed")
    print(f"   ⚔️ Average ilvl: {stats['avg_ilvl']:.1f}")
    print(f"   🏔️ Average M+: {stats['avg_mplus']:.1f}")
    print(f"   📈 Average WCL: {stats['avg_wcl']:.1f}")

if __name__ == "__main__":
    generate_html_dashboard("logs/Player_data.csv")
