import csv
import os
import json
from datetime import datetime

def parse_wcl_from_markdown(content):
    """Extract WCL data from markdown content for both difficulties with rankings"""
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
                        wcl_data[current_difficulty]['boss_rankings'].append({
                            'boss': parts[0],
                            'rank_percent': parts[1].replace('%', '').strip(),
                            'best_amount': int(parts[2].replace(',', '')),
                            'total_kills': int(parts[3])
                        })
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

def get_wcl_color(score):
    """Get WarcraftLogs color based on percentile"""
    try:
        s = float(score)
        if s == 100: return '#e6cc80'
        elif s >= 99: return '#e367a5'
        elif s >= 95: return '#ff8000'
        elif s >= 75: return '#a335ee'
        elif s >= 50: return '#0070dd'
        elif s >= 25: return '#1eff00'
        return '#808080'
    except:
        return '#808080'

def calculate_overall_rank(character_name, all_characters_wcl):
    """Calculate overall rank based on average performance"""
    scores = []
    for char_name, wcl_data in all_characters_wcl.items():
        if not wcl_data.get('has_logs'):
            continue
        
        mythic_perf = wcl_data.get('mythic', {}).get('best_performance', 'N/A')
        try:
            if mythic_perf != 'N/A':
                scores.append((char_name, float(str(mythic_perf).replace(',', ''))))
        except:
            pass
    
    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Find character's rank
    for rank, (name, score) in enumerate(scores, 1):
        if name == character_name:
            return rank, len(scores), score
    
    return None, len(scores), 0

def generate_rankings_html(characters, character_details, character_specs, detailed_dir="detailed"):
    """Generate Rankings tab HTML content"""
    
    # Parse all WCL data
    all_wcl_data = {}
    for fname in os.listdir(detailed_dir):
        if fname.endswith('.md'):
            name = fname[:-3]
            with open(os.path.join(detailed_dir, fname), 'r', encoding='utf-8') as f:
                content = f.read()
                all_wcl_data[name] = parse_wcl_from_markdown(content)
    
    # Filter characters with raid logs
    characters_with_logs = [(c, all_wcl_data.get(c['ID'])) 
                            for c in characters 
                            if c['ID'] in all_wcl_data and all_wcl_data[c['ID']].get('has_logs')]
    
    # Sort by mythic performance
    characters_with_logs.sort(key=lambda x: float(str(x[1].get('mythic', {}).get('best_performance', '0')).replace(',', '')), reverse=True)
    
    html = """
<div id="rankings" class="tab-content">
<h2 style="margin-bottom:20px">🏆 Guild Rankings</h2>

<div class="sort-controls" style="margin-bottom:30px">
<button class="sort-btn active" onclick="switchRankingDifficulty('mythic')">⚔️ Mythic</button>
<button class="sort-btn" onclick="switchRankingDifficulty('heroic')">🛡️ Heroic</button>
</div>
"""
    
    if not characters_with_logs:
        html += '<div style="text-align:center;padding:60px"><h2>No Rankings Available</h2><p>Characters need raid parses on Warcraft Logs</p></div>'
    else:
        for char_info, wcl_data in characters_with_logs:
            name = char_info['ID']
            char_class = char_info['Class']
            spec = char_info.get('Spec', 'Unknown')
            spec_icon = character_specs.get(name, '')
            
            # Get server for profile links
            server = char_info.get('Server', 'azshara')
            
            # Mythic data
            mythic_data = wcl_data.get('mythic', {})
            mythic_perf = mythic_data.get('best_performance', 'N/A')
            mythic_bosses = mythic_data.get('boss_rankings', [])
            
            # Heroic data
            heroic_data = wcl_data.get('heroic', {})
            heroic_perf = heroic_data.get('best_performance', 'N/A')
            heroic_bosses = heroic_data.get('boss_rankings', [])
            
            # Calculate overall rank
            overall_rank, total_chars, avg_score = calculate_overall_rank(name, all_wcl_data)
            
            # All Stars
            all_stars = wcl_data.get('all_stars', [])
            
            # Get color for average performance
            mythic_color = get_wcl_color(mythic_perf if mythic_perf != 'N/A' else 0)
            heroic_color = get_wcl_color(heroic_perf if heroic_perf != 'N/A' else 0)
            
            # Profile links
            wcl_url = f"https://www.warcraftlogs.com/character/kr/{server.lower()}/{name}"
            
            html += f'''
<div class="char-section" style="margin-bottom:40px">
<div class="char-header" style="border-bottom:3px solid {mythic_color}">
'''
            
            if spec_icon:
                html += f'<img src="{spec_icon}" class="char-avatar" onerror="this.style.display=\'none\'">'
            
            html += f'''
<div style="flex:1">
<h3>{name} <span style="color:#666;font-size:0.7em;font-weight:normal">({spec} {char_class})</span></h3>
<div style="display:flex;gap:15px;margin-top:10px;flex-wrap:wrap">
'''
            
            if overall_rank:
                html += f'<span class="badge" style="background:#667eea;color:#fff">Guild Rank: #{overall_rank} / {total_chars}</span>'
            
            html += f'''
<span class="badge" style="background:{mythic_color};color:#fff">Mythic Avg: {mythic_perf}</span>
<span class="badge" style="background:{heroic_color};color:#fff">Heroic Avg: {heroic_perf}</span>
</div>
</div>
<a href="{wcl_url}" target="_blank" title="View on Warcraft Logs" style="padding:12px 20px;background:#ff8000;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;display:flex;align-items:center;gap:8px">
📊 View Logs
</a>
</div>
'''
            
            # All Stars section (always visible)
            if all_stars:
                html += '''
<div style="background:#f0f0f0;padding:20px;border-radius:10px;margin:20px 0">
<h4 style="margin-bottom:15px;display:flex;align-items:center;gap:10px">
<span style="font-size:1.5em">🌟</span> All Stars Rankings
</h4>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:15px">
'''
                
                for star in all_stars:
                    partition = star.get('partition', 'N/A')
                    star_spec = star.get('spec', 'Unknown')
                    points = star.get('points', 0)
                    possible = star.get('possible', 0)
                    rank_pct = star.get('rank_percent', 0)
                    
                    star_color = get_wcl_color(rank_pct)
                    
                    # Calculate percentage of possible points
                    points_pct = (points / possible * 100) if possible > 0 else 0
                    
                    html += f'''
<div style="background:#fff;padding:20px;border-radius:10px;border-left:4px solid {star_color}">
<div style="font-size:0.9em;color:#666;margin-bottom:8px">{partition}</div>
<div style="font-weight:600;font-size:1.1em;margin-bottom:12px">{star_spec}</div>
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
<span style="font-size:1.5em;font-weight:bold;color:{star_color}">{points:.1f}</span>
<span style="color:#666">/ {possible:.1f}</span>
</div>
<div class="perf-bar" style="background:#e0e0e0;height:25px;border-radius:6px;overflow:hidden;margin-bottom:8px">
<div style="height:100%;background:{star_color};width:{points_pct:.1f}%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600;font-size:0.85em">
{points_pct:.1f}%
</div>
</div>
<div style="text-align:center;color:#666;font-size:0.9em">Rank: {rank_pct}%</div>
</div>
'''
                
                html += '</div></div>'
            
            # Boss Rankings table
            html += f'''
<div class="ranking-difficulty-mythic">
<h4 style="margin:25px 0 15px 0;color:#a335ee;display:flex;align-items:center;gap:10px">
<span style="font-size:1.3em">⚔️</span> Mythic Boss Rankings
</h4>
'''
            
            if mythic_bosses:
                html += '''
<div style="overflow-x:auto">
<table style="width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden">
<thead>
<tr style="background:linear-gradient(135deg,#667eea,#764ba2)">
<th style="padding:15px;text-align:left;color:#fff">Boss</th>
<th style="padding:15px;text-align:center;color:#fff">Rank %</th>
<th style="padding:15px;text-align:right;color:#fff">Best DPS/HPS</th>
<th style="padding:15px;text-align:center;color:#fff">Kills</th>
<th style="padding:15px;text-align:left;color:#fff">Performance</th>
</tr>
</thead>
<tbody>
'''
                
                for boss in mythic_bosses:
                    boss_name = boss.get('boss', 'Unknown')
                    rank_pct = boss.get('rank_percent', 0)
                    best_amount = boss.get('best_amount', 0)
                    kills = boss.get('total_kills', 0)
                    
                    try:
                        rank_val = float(rank_pct)
                        boss_color = get_wcl_color(rank_val)
                    except:
                        rank_val = 0
                        boss_color = '#808080'
                    
                    html += f'''
<tr style="border-bottom:1px solid #eee">
<td style="padding:15px;font-weight:600">{boss_name}</td>
<td style="padding:15px;text-align:center">
<span style="display:inline-block;padding:6px 12px;background:{boss_color};color:#fff;border-radius:6px;font-weight:bold">
{rank_pct}%
</span>
</td>
<td style="padding:15px;text-align:right;font-family:monospace;color:#666">{best_amount:,}</td>
<td style="padding:15px;text-align:center">
<span style="display:inline-block;padding:4px 10px;background:#f0f0f0;border-radius:4px;font-weight:600">
{kills}
</span>
</td>
<td style="padding:15px">
<div class="perf-bar" style="background:#e0e0e0;height:25px;border-radius:6px;overflow:hidden;min-width:150px">
<div style="height:100%;background:{boss_color};width:{rank_val}%;display:flex;align-items:center;padding-left:10px;color:#fff;font-weight:600;font-size:0.85em">
{rank_pct}%
</div>
</div>
</td>
</tr>
'''
                
                html += '</tbody></table></div>'
            else:
                html += '<p style="text-align:center;padding:30px;color:#666">No mythic boss kills recorded</p>'
            
            html += '</div>'
            
            # Heroic rankings
            html += f'''
<div class="ranking-difficulty-heroic" style="display:none">
<h4 style="margin:25px 0 15px 0;color:#0070dd;display:flex;align-items:center;gap:10px">
<span style="font-size:1.3em">🛡️</span> Heroic Boss Rankings
</h4>
'''
            
            if heroic_bosses:
                html += '''
<div style="overflow-x:auto">
<table style="width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden">
<thead>
<tr style="background:linear-gradient(135deg,#0070dd,#00a8ff)">
<th style="padding:15px;text-align:left;color:#fff">Boss</th>
<th style="padding:15px;text-align:center;color:#fff">Rank %</th>
<th style="padding:15px;text-align:right;color:#fff">Best DPS/HPS</th>
<th style="padding:15px;text-align:center;color:#fff">Kills</th>
<th style="padding:15px;text-align:left;color:#fff">Performance</th>
</tr>
</thead>
<tbody>
'''
                
                for boss in heroic_bosses:
                    boss_name = boss.get('boss', 'Unknown')
                    rank_pct = boss.get('rank_percent', 0)
                    best_amount = boss.get('best_amount', 0)
                    kills = boss.get('total_kills', 0)
                    
                    try:
                        rank_val = float(rank_pct)
                        boss_color = get_wcl_color(rank_val)
                    except:
                        rank_val = 0
                        boss_color = '#808080'
                    
                    html += f'''
<tr style="border-bottom:1px solid #eee">
<td style="padding:15px;font-weight:600">{boss_name}</td>
<td style="padding:15px;text-align:center">
<span style="display:inline-block;padding:6px 12px;background:{boss_color};color:#fff;border-radius:6px;font-weight:bold">
{rank_pct}%
</span>
</td>
<td style="padding:15px;text-align:right;font-family:monospace;color:#666">{best_amount:,}</td>
<td style="padding:15px;text-align:center">
<span style="display:inline-block;padding:4px 10px;background:#f0f0f0;border-radius:4px;font-weight:600">
{kills}
</span>
</td>
<td style="padding:15px">
<div class="perf-bar" style="background:#e0e0e0;height:25px;border-radius:6px;overflow:hidden;min-width:150px">
<div style="height:100%;background:{boss_color};width:{rank_val}%;display:flex;align-items:center;padding-left:10px;color:#fff;font-weight:600;font-size:0.85em">
{rank_pct}%
</div>
</div>
</td>
</tr>
'''
                
                html += '</tbody></table></div>'
            else:
                html += '<p style="text-align:center;padding:30px;color:#666">No heroic boss kills recorded</p>'
            
            html += '</div></div>'
    
    html += '</div>'
    
    return html

# Update the main generate_html_dashboard function to include Rankings tab
def generate_html_dashboard_with_rankings(csv_file, output_file="dashboard.html", detailed_dir="detailed"):
    """Generate complete dashboard with Rankings tab"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🎨 Generating dashboard with Rankings tab...")
    
    # Read characters
    characters = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        characters = list(csv.DictReader(f))
    
    # Load character details and specs
    character_details = {}
    character_specs = {}
    if os.path.exists(detailed_dir):
        for fname in os.listdir(detailed_dir):
            if fname.endswith('.md'):
                name = fname[:-3]
                with open(os.path.join(detailed_dir, fname), 'r', encoding='utf-8') as f:
                    content = f.read()
                    character_details[name] = content
                    
                    for line in content.split('\n'):
                        if line.startswith('**SPEC_ICON:'):
                            character_specs[name] = line.replace('**SPEC_ICON:', '').replace('**', '').strip()
                            break
    
    # Generate Rankings HTML
    rankings_html = generate_rankings_html(characters, character_details, character_specs, detailed_dir)
    
    # For demonstration, create a simple dashboard structure
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guild Dashboard - Rankings</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box}}
body {{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}}
.container {{max-width:1400px;margin:0 auto}}
header {{text-align:center;color:#fff;margin-bottom:40px;padding:20px}}
h1 {{font-size:3em}}
h2 {{font-size:1.8em;margin-bottom:20px}}
h3 {{font-size:1.4em}}
.tab-container {{background:#fff;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.2);margin-bottom:40px;overflow:hidden}}
.tab-nav {{display:flex;background:#f0f0f0;border-bottom:2px solid #667eea}}
.tab-btn {{flex:1;padding:20px;background:none;border:none;cursor:pointer;font-size:1.1em;font-weight:600;color:#666;transition:all .3s}}
.tab-btn:hover {{background:rgba(102,126,234,.1)}}
.tab-btn.active {{background:#fff;color:#667eea;border-bottom:3px solid #667eea}}
.tab-content {{display:none;padding:30px}}
.tab-content.active {{display:block}}
.sort-controls {{display:flex;gap:15px;margin-bottom:20px;flex-wrap:wrap}}
.sort-btn {{padding:10px 20px;background:#f0f0f0;border:2px solid #667eea;border-radius:8px;cursor:pointer;font-weight:600;color:#667eea;transition:all .3s}}
.sort-btn:hover {{background:#667eea;color:#fff}}
.sort-btn.active {{background:#667eea;color:#fff}}
.char-section {{background:#f8f9fa;border-radius:15px;padding:25px;margin-bottom:30px;border:2px solid #e0e0e0}}
.char-header {{display:flex;align-items:center;margin-bottom:20px;padding-bottom:15px}}
.char-avatar {{width:80px;height:80px;border-radius:10px;margin-right:20px;border:3px solid #667eea}}
.badge {{display:inline-block;padding:6px 12px;border-radius:12px;font-size:.9em;font-weight:600}}
.perf-bar {{height:30px;border-radius:6px;position:relative;overflow:hidden;margin-top:10px}}
footer {{text-align:center;color:#fff;margin-top:40px}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>⚔️ Guild Dashboard</h1>
<p>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</header>
<div class="tab-container">
<div class="tab-nav">
<button class="tab-btn active" onclick="switchTab(event,'rankings')">🏆 Rankings</button>
</div>
{rankings_html}
</div>
<footer><p>두부킴의 유기견들</p></footer>
</div>
<script>
let currentRankingDiff='mythic';
function switchTab(e,t){{
document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
document.querySelectorAll('.tab-btn').forEach(el=>el.classList.remove('active'));
document.getElementById(t).classList.add('active');
e.currentTarget.classList.add('active');
}}
function switchRankingDifficulty(diff){{
currentRankingDiff=diff;
document.querySelectorAll('.sort-controls .sort-btn').forEach(b=>b.classList.remove('active'));
event.target.classList.add('active');
document.querySelectorAll('.ranking-difficulty-mythic').forEach(el=>el.style.display=diff==='mythic'?'block':'none');
document.querySelectorAll('.ranking-difficulty-heroic').forEach(el=>el.style.display=diff==='heroic'?'block':'none');
}}
</script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard with Rankings generated: {output_file}")
    print("   - Guild Rankings with All Stars")
    print("   - Per-boss performance with visual bars")
    print("   - Mythic/Heroic difficulty switching")

if __name__ == "__main__":
    generate_html_dashboard_with_rankings("logs/Player_data.csv")
