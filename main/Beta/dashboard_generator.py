#!/usr/bin/env python3
"""
Complete WoW Audit-Style Dashboard
Includes ALL tabs: Summary, Overview, Great Vault & Gear, Roster, Raids, M+ Details, Professions
"""

import csv
import os
import json
from datetime import datetime
from collections import Counter

def load_character_data(csv_file="logs/Player_data.csv"):
    """Load character data from CSV"""
    if not os.path.exists(csv_file):
        return []
    with open(csv_file, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def load_detailed_data(detailed_dir="detailed"):
    """Load detailed character data"""
    details = {}
    specs = {}
    equipment = {}
    wcl_data = {}
    
    if not os.path.exists(detailed_dir):
        return details, specs, equipment, wcl_data
    
    for fname in os.listdir(detailed_dir):
        if fname.endswith('.md'):
            name = fname[:-3]
            with open(os.path.join(detailed_dir, fname), 'r', encoding='utf-8') as f:
                content = f.read()
                details[name] = content
                
                # Extract spec icon
                for line in content.split('\n'):
                    if line.startswith('**SPEC_ICON:'):
                        specs[name] = line.replace('**SPEC_ICON:', '').replace('**', '').strip()
                        break
                
                # Parse equipment and WCL data
                equipment[name] = parse_equipment(content)
                wcl_data[name] = parse_wcl_data(content)
    
    return details, specs, equipment, wcl_data

def parse_equipment(content):
    """Parse equipment from markdown"""
    equipment = []
    in_equipment = False
    
    for line in content.split('\n'):
        if '## ⚔️ Equipment' in line:
            in_equipment = True
            continue
        
        if in_equipment and line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 3 and parts[0] not in ['Slot', '']:
                try:
                    equipment.append({
                        'slot': parts[0],
                        'name': parts[1],
                        'ilvl': int(parts[2]) if parts[2].isdigit() else 0,
                        'upgrade': parts[3] if len(parts) > 3 else 'Unknown'
                    })
                except:
                    pass
        
        if in_equipment and line.startswith('---'):
            break
    
    return equipment

def parse_wcl_data(content):
    """Parse WCL data from markdown"""
    wcl = {'mythic': [], 'heroic': []}
    current_difficulty = None
    in_boss_table = False
    
    for line in content.split('\n'):
        if '## 🏆 WarcraftLogs Performance - Mythic' in line:
            current_difficulty = 'mythic'
            in_boss_table = False
            continue
        
        if '## 🏆 WarcraftLogs Performance - Heroic' in line:
            current_difficulty = 'heroic'
            in_boss_table = False
            continue
        
        if current_difficulty and '### 📋 Boss Rankings' in line:
            in_boss_table = True
            continue
        
        if in_boss_table and line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4 and parts[0] not in ['Boss', '']:
                try:
                    wcl[current_difficulty].append({
                        'boss': parts[0],
                        'rank_percent': float(parts[1].replace('%', '').strip()),
                        'best_amount': int(parts[2].replace(',', '')) if parts[2] != 'N/A' else 0,
                        'total_kills': int(parts[3]) if parts[3].isdigit() else 0
                    })
                except:
                    pass
        
        if line.startswith('---') or line.startswith('##'):
            in_boss_table = False
    
    return wcl

def get_class_color(char_class):
    """WoW class colors"""
    colors = {
        'Warrior': '#C69B6D', 'Paladin': '#F48CBA', 'Hunter': '#AAD372',
        'Rogue': '#FFF468', 'Priest': '#FFFFFF', 'Deathknight': '#C41E3A',
        'Death Knight': '#C41E3A', 'Shaman': '#0070DD', 'Mage': '#3FC7EB',
        'Warlock': '#8788EE', 'Monk': '#00FF98', 'Druid': '#FF7C0A',
        'Demon Hunter': '#A330C9', 'Demonhunter': '#A330C9', 'Evoker': '#33937F'
    }
    return colors.get(char_class, '#667eea')

def generate_complete_dashboard(csv_file="logs/Player_data.csv", output_file="dashboard_complete.html"):
    """Generate complete WoW Audit-style dashboard with all tabs"""
    
    print("🎨 Generating COMPLETE WoW Audit-style dashboard with ALL tabs...")
    
    # Load all data
    characters = load_character_data(csv_file)
    if not characters:
        print("❌ No character data found")
        return
    
    details, specs, equipment, wcl_data = load_detailed_data("detailed")
    
    # Load M+ data
    mplus_data = {}
    if os.path.exists("logs/mplus_enhanced.json"):
        with open("logs/mplus_enhanced.json", 'r') as f:
            mplus_data = json.load(f)
    
    # Calculate stats
    total = len(characters)
    ilvls = [float(c['ilvl']) for c in characters if c['ilvl'] != 'N/A']
    mplus_scores = [float(str(c['M+']).replace(',', '')) for c in characters if c['M+'] != 'N/A']
    wcl_scores = [float(str(c['WCL']).replace(',', '')) for c in characters if c['WCL'] != 'N/A']
    
    avg_ilvl = sum(ilvls)/len(ilvls) if ilvls else 0
    avg_mplus = sum(mplus_scores)/len(mplus_scores) if mplus_scores else 0
    avg_wcl = sum(wcl_scores)/len(wcl_scores) if wcl_scores else 0
    max_ilvl = max(ilvls) if ilvls else 730
    min_ilvl = min(ilvls) if ilvls else 700
    
    # Class distribution
    class_counts = Counter([c['Class'] for c in characters])
    
    # Sort characters
    characters_sorted = sorted(characters, key=lambda x: float(x['ilvl']) if x['ilvl'] != 'N/A' else 0, reverse=True)
    
    # Start HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guild Dashboard - WoW Audit Complete</title>
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #1a1a1a;
    color: #e0e0e0;
}}

.header {{
    background: linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%);
    padding: 20px;
    border-bottom: 3px solid #4a90e2;
    box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    position: sticky;
    top: 0;
    z-index: 100;
}}

.header-content {{
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.guild-name {{
    font-size: 2em;
    font-weight: bold;
    color: #4a90e2;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}}

.last-updated {{
    color: #888;
    font-size: 0.9em;
}}

.tabs {{
    background: #2c2c2c;
    border-bottom: 2px solid #333;
    position: sticky;
    top: 83px;
    z-index: 99;
}}

.tabs-content {{
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    overflow-x: auto;
}}

.tab-button {{
    padding: 15px 25px;
    background: none;
    border: none;
    color: #888;
    cursor: pointer;
    font-size: 0.95em;
    font-weight: 600;
    border-bottom: 3px solid transparent;
    transition: all 0.3s;
    white-space: nowrap;
}}

.tab-button:hover {{
    background: #333;
    color: #4a90e2;
}}

.tab-button.active {{
    color: #4a90e2;
    border-bottom-color: #4a90e2;
    background: #1a1a1a;
}}

.container {{
    max-width: 1400px;
    margin: 20px auto;
    padding: 0 20px;
}}

.tab-content {{
    display: none;
}}

.tab-content.active {{
    display: block;
}}

.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}}

.stat-card {{
    background: #2c2c2c;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #333;
    text-align: center;
}}

.stat-label {{
    color: #888;
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
}}

.stat-value {{
    font-size: 2.5em;
    font-weight: bold;
    color: #4a90e2;
}}

.table-container {{
    background: #2c2c2c;
    border-radius: 10px;
    overflow-x: auto;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}

table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 800px;
}}

thead {{
    background: #1a1a1a;
    position: sticky;
    top: 145px;
    z-index: 10;
}}

th {{
    padding: 12px 8px;
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75em;
    letter-spacing: 0.5px;
    color: #4a90e2;
    border-bottom: 2px solid #4a90e2;
    cursor: pointer;
    white-space: nowrap;
}}

th:hover {{
    background: #333;
}}

td {{
    padding: 10px 8px;
    border-bottom: 1px solid #333;
    font-size: 0.9em;
}}

tr:hover {{
    background: #252525;
}}

.class-icon {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    display: inline-block;
    margin-right: 6px;
    vertical-align: middle;
}}

.spec-icon {{
    width: 20px;
    height: 20px;
    border-radius: 3px;
    margin-right: 4px;
    vertical-align: middle;
    border: 1px solid #333;
}}

.score-badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 3px;
    font-weight: 600;
    font-size: 0.85em;
}}

.score-high {{ background: #10b981; color: white; }}
.score-medium {{ background: #3b82f6; color: white; }}
.score-low {{ background: #6b7280; color: white; }}

.clickable {{
    color: #4a90e2;
    cursor: pointer;
    text-decoration: none;
}}

.clickable:hover {{
    text-decoration: underline;
}}

.section-title {{
    font-size: 1.5em;
    color: #4a90e2;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #333;
}}

.equipment-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 15px;
}}

.equipment-slot {{
    background: #1a1a1a;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #4a90e2;
}}

.slot-name {{
    font-size: 0.8em;
    color: #888;
    text-transform: uppercase;
    margin-bottom: 5px;
}}

.item-name {{
    font-weight: 600;
    margin-bottom: 5px;
}}

.item-ilvl {{
    font-size: 1.2em;
    font-weight: bold;
    color: #4a90e2;
    display: inline-block;
    margin-right: 10px;
}}

.item-upgrade {{
    font-size: 0.9em;
    color: #10b981;
}}

.class-breakdown {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
}}

.class-card {{
    background: #1a1a1a;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}}

.class-name {{
    font-weight: 600;
    margin-bottom: 10px;
}}

.class-count {{
    font-size: 2em;
    font-weight: bold;
    color: #4a90e2;
}}

.boss-row {{
    background: #1a1a1a;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.boss-name {{
    font-weight: 600;
    font-size: 1.1em;
}}

.boss-stats {{
    display: flex;
    gap: 20px;
    align-items: center;
}}

.boss-kills {{
    color: #10b981;
    font-weight: 600;
}}

.boss-perf {{
    font-size: 1.3em;
    font-weight: bold;
    color: #4a90e2;
}}

@media (max-width: 768px) {{
    .stats-grid {{
        grid-template-columns: repeat(2, 1fr);
    }}
    
    .equipment-grid {{
        grid-template-columns: 1fr;
    }}
    
    table {{
        font-size: 0.8em;
    }}
    
    th, td {{
        padding: 8px 4px;
    }}
}}
</style>
</head>
<body>

<div class="header">
    <div class="header-content">
        <div>
            <div class="guild-name">⚔️ 두부킴의 유기견들</div>
            <div class="last-updated">Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
    </div>
</div>

<div class="tabs">
    <div class="tabs-content">
        <button class="tab-button active" onclick="showTab('summary')">📊 Summary</button>
        <button class="tab-button" onclick="showTab('overview')">📋 Overview</button>
        <button class="tab-button" onclick="showTab('gear')">⚔️ Great Vault & Gear</button>
        <button class="tab-button" onclick="showTab('roster')">👥 Roster</button>
        <button class="tab-button" onclick="showTab('raids')">🏆 Raids</button>
        <button class="tab-button" onclick="showTab('mplus')">🏔️ M+ Details</button>
    </div>
</div>

<div class="container">

<!-- TAB 1: SUMMARY -->
<div id="summary" class="tab-content active">
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Members</div>
            <div class="stat-value">{total}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Average ilvl</div>
            <div class="stat-value">{avg_ilvl:.1f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Average M+ Score</div>
            <div class="stat-value">{avg_mplus:.0f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Average WCL</div>
            <div class="stat-value">{avg_wcl:.1f}</div>
        </div>
    </div>
    
    <div class="section-title">Guild Summary</div>
    <div class="stats-grid">
"""
    
    # Add more summary stats
    highest_ilvl = max(ilvls) if ilvls else 0
    highest_mplus = max(mplus_scores) if mplus_scores else 0
    highest_wcl = max(wcl_scores) if wcl_scores else 0
    
    html += f"""
        <div class="stat-card">
            <div class="stat-label">Highest ilvl</div>
            <div class="stat-value">{highest_ilvl:.0f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Highest M+</div>
            <div class="stat-value">{highest_mplus:.0f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Highest WCL</div>
            <div class="stat-value">{highest_wcl:.1f}</div>
        </div>
    </div>
</div>

<!-- TAB 2: OVERVIEW -->
<div id="overview" class="tab-content">
    <div class="section-title">Character Overview</div>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th style="width:50px;">Rank</th>
                    <th>Character</th>
                    <th>Class</th>
                    <th>Spec</th>
                    <th>ilvl</th>
                    <th>M+ Score</th>
                    <th>WCL</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add character rows to Overview
    for idx, char in enumerate(characters_sorted, 1):
        name = char['ID']
        char_class = char['Class']
        spec = char['Spec']
        ilvl = char['ilvl']
        mplus = char['M+']
        wcl = char['WCL']
        
        class_color = get_class_color(char_class)
        spec_icon = specs.get(name, '')
        
        # M+ Score badge
        try:
            mplus_val = float(str(mplus).replace(',', ''))
            mplus_class = 'score-high' if mplus_val >= 3000 else 'score-medium' if mplus_val >= 2500 else 'score-low'
            mplus_display = f'<span class="score-badge {mplus_class}">{mplus_val:.0f}</span>'
        except:
            mplus_display = '<span class="score-badge score-low">N/A</span>'
        
        # WCL badge
        try:
            wcl_val = float(str(wcl).replace(',', ''))
            wcl_class = 'score-high' if wcl_val >= 90 else 'score-medium' if wcl_val >= 75 else 'score-low'
            wcl_display = f'<span class="score-badge {wcl_class}">{wcl_val:.1f}</span>'
        except:
            wcl_display = '<span class="score-badge score-low">N/A</span>'
        
        spec_cell = f'<img src="{spec_icon}" class="spec-icon" onerror="this.style.display=\'none\'">{spec}' if spec_icon else spec
        
        html += f"""
                <tr>
                    <td style="color:#888;font-weight:600;">#{idx}</td>
                    <td><span class="clickable" onclick="alert('Details for {name}')">{name}</span></td>
                    <td><span class="class-icon" style="background-color:{class_color};"></span>{char_class}</td>
                    <td>{spec_cell}</td>
                    <td style="font-weight:600;color:#4a90e2;">{ilvl}</td>
                    <td>{mplus_display}</td>
                    <td>{wcl_display}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
</div>

<!-- TAB 3: GREAT VAULT & GEAR -->
<div id="gear" class="tab-content">
    <div class="section-title">Great Vault & Equipment</div>
"""
    
    # Show equipment for each character
    for char in characters_sorted[:10]:  # Show top 10
        name = char['ID']
        if name in equipment and equipment[name]:
            html += f"""
    <div style="margin-bottom:30px;">
        <h3 style="color:#4a90e2;margin-bottom:15px;">{name} - Equipment</h3>
        <div class="equipment-grid">
"""
            for item in equipment[name]:
                html += f"""
            <div class="equipment-slot">
                <div class="slot-name">{item['slot']}</div>
                <div class="item-name">{item['name']}</div>
                <div>
                    <span class="item-ilvl">{item['ilvl']}</span>
                    <span class="item-upgrade">{item['upgrade']}</span>
                </div>
            </div>
"""
            html += """
        </div>
    </div>
"""
    
    html += """
</div>

<!-- TAB 4: ROSTER -->
<div id="roster" class="tab-content">
    <div class="section-title">Guild Roster - Class Breakdown</div>
    <div class="class-breakdown">
"""
    
    # Class breakdown
    for char_class, count in class_counts.most_common():
        class_color = get_class_color(char_class)
        html += f"""
        <div class="class-card">
            <div class="class-name" style="color:{class_color};">
                <span class="class-icon" style="background-color:{class_color};"></span>
                {char_class}
            </div>
            <div class="class-count">{count}</div>
        </div>
"""
    
    html += """
    </div>
</div>

<!-- TAB 5: RAIDS -->
<div id="raids" class="tab-content">
    <div class="section-title">Raid Performance - Mythic</div>
"""
    
    # Show raid data for characters with WCL data
    for char in characters_sorted:
        name = char['ID']
        if name in wcl_data and wcl_data[name]['mythic']:
            html += f"""
    <div style="margin-bottom:30px;">
        <h3 style="color:#4a90e2;margin-bottom:15px;">{name}</h3>
"""
            for boss in wcl_data[name]['mythic']:
                rank_color = '#10b981' if boss['rank_percent'] >= 90 else '#3b82f6' if boss['rank_percent'] >= 75 else '#6b7280'
                html += f"""
        <div class="boss-row">
            <div class="boss-name">{boss['boss']}</div>
            <div class="boss-stats">
                <div class="boss-kills">{boss['total_kills']} kills</div>
                <div class="boss-perf" style="color:{rank_color};">{boss['rank_percent']:.1f}%</div>
            </div>
        </div>
"""
            html += """
    </div>
"""
    
    if not any(wcl_data[c['ID']]['mythic'] for c in characters_sorted if c['ID'] in wcl_data):
        html += '<p style="color:#888;text-align:center;padding:40px;">No mythic raid data available yet.</p>'
    
    html += """
</div>

<!-- TAB 6: M+ DETAILS -->
<div id="mplus" class="tab-content">
    <div class="section-title">Mythic+ Recent Runs</div>
"""
    
    # Show M+ data
    if mplus_data:
        for name, data in sorted(mplus_data.items(), key=lambda x: x[1].get('character', {}).get('score', 0), reverse=True):
            char_info = data.get('character', {})
            runs = data.get('best_runs', [])[:5]  # Top 5 runs
            
            if runs:
                html += f"""
    <div style="margin-bottom:30px;">
        <h3 style="color:#4a90e2;margin-bottom:15px;">{name} - M+ Score: {char_info.get('score', 0):.0f}</h3>
"""
                for run in runs:
                    level = run.get('level', 0)
                    dungeon = run.get('dungeon', 'Unknown')
                    score = run.get('score', 0)
                    timed = run.get('timed', False)
                    upgrade = run.get('upgrade_text', '')
                    
                    status_color = '#10b981' if timed else '#ef4444'
                    status_text = '✅ Timed' if timed else '❌ Depleted'
                    
                    html += f"""
        <div class="boss-row">
            <div>
                <div class="boss-name">{dungeon} +{level} {upgrade}</div>
                <div style="font-size:0.9em;color:#888;margin-top:4px;">Score: {score:.1f}</div>
            </div>
            <div style="color:{status_color};font-weight:600;">{status_text}</div>
        </div>
"""
                html += """
    </div>
"""
    else:
        html += '<p style="color:#888;text-align:center;padding:40px;">Run <code>python mplus_enhanced.py</code> to fetch M+ details.</p>'
    
    html += """
</div>

</div>

<script>
function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remove active from all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Activate button
    event.target.classList.add('active');
}
</script>

</body>
</html>
"""
    
    # Write HTML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Complete WoW Audit-style dashboard generated!")
    print(f"   📁 File: {output_file}")
    print(f"   📊 {total} characters")
    print(f"   📋 6 tabs: Summary, Overview, Gear, Roster, Raids, M+")
    print(f"   🎨 WoW Audit dark theme styling")

if __name__ == "__main__":
    generate_complete_dashboard()
