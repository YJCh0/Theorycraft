"""
Enhanced dashboard generator with all new features
Save as: generate_dashboard_enhanced.py
Integrates with your existing generate_html_dashboard.py
"""
import csv
import os
import json
from datetime import datetime
from guild_analytics import GuildAnalytics

def generate_enhanced_dashboard(csv_file="logs/Player_data.csv", 
                                enhanced_file="logs/characters_enhanced.json",
                                analytics_file="logs/guild_analytics.json",
                                output_file="dashboard.html"):
    """Generate enhanced dashboard with 7 tabs"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🎨 Generating enhanced dashboard...")
    
    # Load all data
    with open(csv_file, 'r', encoding='utf-8') as f:
        characters = list(csv.DictReader(f))
    
    enhanced_data = {}
    if os.path.exists(enhanced_file):
        with open(enhanced_file, 'r') as f:
            enhanced_list = json.load(f)
            enhanced_data = {c['name']: c for c in enhanced_list}
    
    analytics_data = {}
    if os.path.exists(analytics_file):
        with open(analytics_file, 'r') as f:
            analytics_data = json.load(f)
    
    # Load history
    try:
        from history_tracker import get_guild_average_history, get_top_improvers
        guild_history = get_guild_average_history()
        top_improvers = get_top_improvers(7)
    except:
        guild_history = {'dates': [], 'avg_ilvl': [], 'avg_mplus': [], 'avg_wcl': []}
        top_improvers = []
    
    # Calculate stats
    total = len(characters)
    ilvls = [float(c['ilvl']) for c in characters if c['ilvl'] != 'N/A']
    mplus_scores = [float(str(c['M+']).replace(',', '')) for c in characters if c['M+'] != 'N/A']
    wcl_scores = [float(str(c['WCL']).replace(',', '')) for c in characters if c['WCL'] != 'N/A']
    
    avg_ilvl = sum(ilvls)/len(ilvls) if ilvls else 0
    avg_mplus = sum(mplus_scores)/len(mplus_scores) if mplus_scores else 0
    avg_wcl = sum(wcl_scores)/len(wcl_scores) if wcl_scores else 0
    
    # Prepare chart data
    names = [c['ID'] for c in characters]
    ilvl_data = [float(c['ilvl']) if c['ilvl']!='N/A' else 0 for c in characters]
    mplus_data_chart = [float(str(c['M+']).replace(',','')) if c['M+']!='N/A' else 0 for c in characters]
    wcl_data_chart = [float(str(c['WCL']).replace(',','')) if c['WCL']!='N/A' else 0 for c in characters]
    
    class_colors = {
        'Deathknight':'#C41E3A','Demon Hunter':'#A330C9','Druid':'#FF7C0A',
        'Evoker':'#33937F','Hunter':'#AAD372','Mage':'#3FC7EB',
        'Monk':'#00FF98','Paladin':'#F48CBA','Priest':'#FFFFFF',
        'Rogue':'#FFF468','Shaman':'#0070DD','Warlock':'#8788EE',
        'Warrior':'#C69B6D','Demonhunter':'#A330C9'
    }
    
    colors = [class_colors.get(c['Class'],'#667eea') for c in characters]
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Enhanced Guild Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}}
.container{{max-width:1600px;margin:0 auto}}
header{{text-align:center;color:#fff;margin-bottom:40px;padding:20px}}
h1{{font-size:3em;text-shadow:2px 2px 4px rgba(0,0,0,0.3)}}
h2{{font-size:1.8em;margin-bottom:20px;color:#667eea}}
h3{{font-size:1.4em;color:#667eea;margin:20px 0 10px}}

.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}}
.stat-card{{background:#fff;border-radius:15px;padding:25px;box-shadow:0 10px 30px rgba(0,0,0,.2);transition:transform 0.3s}}
.stat-card:hover{{transform:translateY(-5px)}}
.value{{font-size:2.5em;font-weight:bold;color:#667eea}}
.label{{color:#666;font-size:0.9em;margin-top:5px}}

.tab-container{{background:#fff;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.2);margin-bottom:40px;overflow:hidden}}
.tab-nav{{display:flex;background:#f0f0f0;border-bottom:3px solid #667eea;overflow-x:auto}}
.tab-btn{{flex:1;min-width:120px;padding:20px;background:none;border:none;cursor:pointer;font-size:1em;font-weight:600;color:#666;transition:all .3s;white-space:nowrap}}
.tab-btn:hover{{background:rgba(102,126,234,.1)}}
.tab-btn.active{{background:#fff;color:#667eea;border-bottom:3px solid #667eea}}
.tab-content{{display:none;padding:30px;max-height:80vh;overflow-y:auto}}
.tab-content.active{{display:block}}

.chart-container{{position:relative;height:500px;padding:20px;background:#fff;border-radius:10px;border:2px solid #e0e0e0;margin-bottom:30px}}

table{{width:100%;border-collapse:collapse;margin:20px 0}}
th{{background:#667eea;color:#fff;padding:12px;text-align:left;position:sticky;top:0;z-index:10}}
td{{padding:12px;border-bottom:1px solid #eee}}
tr:hover{{background:#f8f9ff}}

.badge{{display:inline-block;padding:4px 12px;border-radius:12px;font-size:.85em;font-weight:600;color:#fff}}

.recommendation-card{{background:#fff3cd;border-left:4px solid:#ffc107;padding:15px;margin:10px 0;border-radius:8px}}
.recommendation-card.warning{{background:#f8d7da;border-left-color:#dc3545}}
.recommendation-card.info{{background:#d1ecf1;border-left-color:#17a2b8}}

.comp-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;margin:20px 0}}
.comp-section{{background:#f8f9fa;padding:20px;border-radius:10px;border:2px solid #667eea}}
.comp-section h4{{color:#667eea;margin-bottom:15px}}
.member-card{{background:#fff;padding:10px;margin:8px 0;border-radius:6px;border-left:3px solid #667eea}}

.progress-bar{{height:30px;background:#e0e0e0;border-radius:6px;overflow:hidden;margin:10px 0}}
.progress-fill{{height:100%;background:linear-gradient(90deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600;transition:width 0.5s}}

.consistency-badge{{padding:3px 8px;border-radius:4px;font-size:0.75em;font-weight:600}}
.consistency-excellent{{background:#28a745;color:#fff}}
.consistency-good{{background:#ffc107;color:#000}}
.consistency-poor{{background:#dc3545;color:#fff}}

@media(max-width:768px){{
body{{padding:10px}}
h1{{font-size:1.8em}}
.stats-grid{{grid-template-columns:repeat(2,1fr);gap:10px}}
.tab-btn{{padding:12px 8px;font-size:0.85em}}
.chart-container{{height:300px}}
}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>⚔️ Enhanced Guild Dashboard</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</header>

<div class="stats-grid">
<div class="stat-card">
<div class="value">{total}</div>
<div class="label">👥 Total Members</div>
</div>
<div class="stat-card">
<div class="value">{avg_ilvl:.1f}</div>
<div class="label">⚔️ Average ilvl</div>
</div>
<div class="stat-card">
<div class="value">{avg_mplus:.0f}</div>
<div class="label">🏔️ Average M+ Score</div>
</div>
<div class="stat-card">
<div class="value">{avg_wcl:.1f}</div>
<div class="label">📈 Average WCL Parse</div>
</div>
</div>

<div class="tab-container">
<div class="tab-nav">
<button class="tab-btn active" onclick="switchTab(event,'overview')">📊 Overview</button>
<button class="tab-btn" onclick="switchTab(event,'roster')">📋 Roster</button>
<button class="tab-btn" onclick="switchTab(event,'analytics')">🎯 Analytics</button>
<button class="tab-btn" onclick="switchTab(event,'raiding')">🏆 Raiding</button>
<button class="tab-btn" onclick="switchTab(event,'mplus')">🏔️ M+</button>
<button class="tab-btn" onclick="switchTab(event,'composition')">🛡️ Composition</button>
<button class="tab-btn" onclick="switchTab(event,'trends')">📈 Trends</button>
</div>

<!-- OVERVIEW TAB -->
<div id="overview" class="tab-content active">
<h2>Guild Progress Overview</h2>
<div class="chart-container">
<canvas id="trendChart"></canvas>
</div>

<h2>🏆 Top Improvers (Last 7 Days)</h2>
<table>
<thead><tr><th>Rank</th><th>Character</th><th>Spec</th><th>ilvl Δ</th><th>M+ Δ</th><th>WCL Δ</th></tr></thead>
<tbody>
"""
    
    # Top improvers
    if top_improvers:
        for i, p in enumerate(top_improvers[:10], 1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            html += f"""<tr>
<td><b>{medal}</b></td>
<td><b>{p['name']}</b></td>
<td>{p['spec']} {p['class']}</td>
<td style="color:#28a745">+{p['ilvl_gain']:.1f}</td>
<td style="color:#28a745">+{p['mplus_gain']:.0f}</td>
<td style="color:#28a745">+{p['wcl_gain']:.1f}</td>
</tr>"""
    
    html += """</tbody></table>
</div>

<!-- ROSTER TAB -->
<div id="roster" class="tab-content">
<h2>Character Roster</h2>
<table>
<thead><tr><th>Name</th><th>Class</th><th>Spec</th><th>ilvl</th><th>M+</th><th>WCL</th><th>Readiness</th></tr></thead>
<tbody>
"""
    
    # Roster with readiness
    for c in characters:
        name = c['ID']
        enhanced = enhanced_data.get(name, {})
        readiness = enhanced.get('readiness', {})
        readiness_score = readiness.get('score', 0)
        readiness_color = '#28a745' if readiness_score >= 85 else '#ffc107' if readiness_score >= 70 else '#dc3545'
        
        html += f"""<tr>
<td><b>{name}</b></td>
<td>{c['Class']}</td>
<td>{c['Spec']}</td>
<td>{c['ilvl']}</td>
<td>{c['M+']}</td>
<td>{c['WCL']}</td>
<td><span class="badge" style="background:{readiness_color}">{readiness_score:.0f}</span></td>
</tr>"""
    
    # ANALYTICS TAB
    html += """</tbody></table>
</div>

<div id="analytics" class="tab-content">
<h2>🎯 Guild Analytics & Recommendations</h2>
"""
    
    if analytics_data:
        # Performance analysis
        perf = analytics_data.get('performance_analysis', {})
        html += f"""
<h3>Performance Distribution</h3>
<div class="stats-grid">
<div class="stat-card">
<div class="value">{len(perf.get('performance_tiers', {}).get('excellent', []))}</div>
<div class="label">🌟 Excellent (95+)</div>
</div>
<div class="stat-card">
<div class="value">{len(perf.get('performance_tiers', {}).get('good', []))}</div>
<div class="label">✅ Good (75-94)</div>
</div>
<div class="stat-card">
<div class="value">{len(perf.get('performance_tiers', {}).get('average', []))}</div>
<div class="label">📊 Average (50-74)</div>
</div>
<div class="stat-card">
<div class="value">{len(perf.get('performance_tiers', {}).get('needs_work', []))}</div>
<div class="label">📚 Needs Work (<50)</div>
</div>
</div>
"""
        
        # Recommendations
        recommendations = analytics_data.get('recommendations', [])
        if recommendations:
            html += "<h3>💡 Recommendations</h3>"
            for rec in recommendations:
                card_class = 'warning' if '⚠️' in rec else 'info' if 'ℹ️' in rec else ''
                html += f'<div class="recommendation-card {card_class}">{rec}</div>'
    
    html += """</div>

<!-- RAIDING TAB -->
<div id="raiding" class="tab-content">
<h2>🏆 Raid Performance Analysis</h2>
<div class="chart-container">
<canvas id="performanceChart"></canvas>
</div>

<h3>Consistency Scores</h3>
<table>
<thead><tr><th>Character</th><th>Consistency</th><th>Best Boss</th><th>Needs Work</th></tr></thead>
<tbody>
"""
    
    # Raid performance details
    for name, data in enhanced_data.items():
        consistency = data.get('consistency', {})
        if consistency.get('total_bosses', 0) > 0:
            rating = consistency.get('consistency_rating', 'Unknown')
            badge_class = 'consistency-excellent' if rating == 'Excellent' else 'consistency-good' if rating in ['Good', 'Average'] else 'consistency-poor'
            
            html += f"""<tr>
<td><b>{name}</b></td>
<td><span class="consistency-badge {badge_class}">{rating} ({consistency.get('average_consistency', 0):.0f}%)</span></td>
<td>{consistency.get('best_boss', 'N/A')}</td>
<td>{consistency.get('worst_boss', 'N/A')}</td>
</tr>"""
    
    html += """</tbody></table>
</div>

<!-- M+ TAB -->
<div id="mplus" class="tab-content">
<h2>🏔️ Mythic+ Performance</h2>
<div class="chart-container">
<canvas id="mplusChart"></canvas>
</div>
</div>

<!-- COMPOSITION TAB -->
<div id="composition" class="tab-content">
<h2>🛡️ Roster Composition Analysis</h2>
"""
    
    if analytics_data:
        comp = analytics_data.get('roster_composition', {})
        roles = comp.get('by_role', {})
        
        html += f"""
<div class="stats-grid">
<div class="stat-card">
<div class="value">{roles.get('Tank', 0)}</div>
<div class="label">🛡️ Tanks</div>
</div>
<div class="stat-card">
<div class="value">{roles.get('Healer', 0)}</div>
<div class="label">💚 Healers</div>
</div>
<div class="stat-card">
<div class="value">{roles.get('Melee', 0)}</div>
<div class="label">⚔️ Melee DPS</div>
</div>
<div class="stat-card">
<div class="value">{roles.get('Ranged', 0)}</div>
<div class="label">🏹 Ranged DPS</div>
</div>
</div>

<h3>Suggested Mythic Composition</h3>
"""
        
        mythic_comp = analytics_data.get('suggested_mythic_comp', {})
        if mythic_comp:
            html += '<div class="comp-grid">'
            
            for role_name, members in [('Tanks', 'tanks'), ('Healers', 'healers'), ('Melee DPS', 'melee'), ('Ranged DPS', 'ranged')]:
                html += f'<div class="comp-section"><h4>{role_name}</h4>'
                for member in mythic_comp.get(members, []):
                    html += f'<div class="member-card"><b>{member["name"]}</b><br>{member["spec"]} {member["class"]}<br><small>Readiness: {member.get("readiness", 0):.0f}</small></div>'
                html += '</div>'
            
            html += '</div>'
    
    html += """</div>

<!-- TRENDS TAB -->
<div id="trends" class="tab-content">
<h2>📈 Historical Trends</h2>
<div class="chart-container">
<canvas id="historyChart"></canvas>
</div>
</div>

</div>

<footer style="text-align:center;color:#fff;margin-top:40px;padding:20px">
<p>두부킴의 유기견들 | Enhanced Dashboard v2.0</p>
</footer>
</div>

<script>
function switchTab(e,t){
document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
document.querySelectorAll('.tab-btn').forEach(el=>el.classList.remove('active'));
document.getElementById(t).classList.add('active');
e.currentTarget.classList.add('active');
}

const chartBg={
beforeDraw:c=>{
const x=c.ctx;
x.save();
x.fillStyle='#f8f9fa';
x.fillRect(0,0,c.width,c.height);
x.restore();
}
};

// Trend Chart
new Chart(document.getElementById('trendChart'),{
type:'line',
data:{
labels:{json.dumps(guild_history['dates'])},
datasets:[
{label:'ilvl',data:{json.dumps(guild_history['avg_ilvl'])},borderColor:'#667eea',tension:.4},
{label:'M+',data:{json.dumps(guild_history['avg_mplus'])},borderColor:'#FF6B6B',tension:.4},
{label:'WCL',data:{json.dumps(guild_history['avg_wcl'])},borderColor:'#4ECDC4',tension:.4}
]
},
options:{
responsive:true,
maintainAspectRatio:false,
plugins:{legend:{display:true}}
},
plugins:[chartBg]
});

// Performance Distribution Chart
new Chart(document.getElementById('performanceChart'),{
type:'bar',
data:{
labels:{json.dumps(names)},
datasets:[{
label:'WCL Performance',
data:{json.dumps(wcl_data_chart)},
backgroundColor:{json.dumps(colors)}
}}]
},
options:{
responsive:true,
maintainAspectRatio:false,
plugins:{legend:{display:false}}
},
plugins:[chartBg]
});

// M+ Chart
new Chart(document.getElementById('mplusChart'),{
type:'bar',
data:{
labels:{json.dumps(names)},
datasets:[{
label:'M+ Score',
data:{json.dumps(mplus_data_chart)},
backgroundColor:{json.dumps(colors)}
}}]
},
options:{
responsive:true,
maintainAspectRatio:false,
plugins:{legend:{display:false}}
},
plugins:[chartBg]
});

// History Chart
new Chart(document.getElementById('historyChart'),{
type:'line',
data:{
labels:{json.dumps(guild_history['dates'])},
datasets:[
{label:'Avg ilvl',data:{json.dumps(guild_history['avg_ilvl'])},borderColor:'#667eea',fill:true,backgroundColor:'rgba(102,126,234,0.1)'},
{label:'Avg M+',data:{json.dumps(guild_history['avg_mplus'])},borderColor:'#FF6B6B',fill:true,backgroundColor:'rgba(255,107,107,0.1)'},
{label:'Avg WCL',data:{json.dumps(guild_history['avg_wcl'])},borderColor:'#4ECDC4',fill:true,backgroundColor:'rgba(78,205,196,0.1)'}
]
},
options:{
responsive:true,
maintainAspectRatio:false,
plugins:{legend:{display:true}}
},
plugins:[chartBg]
});
</script>
</body>
</html>"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Enhanced dashboard generated: {output_file}")
    print(f"   📊 7 tabs with comprehensive analytics")
    print(f"   🎯 Guild recommendations included")
    print(f"   📈 Performance consistency tracking")


if __name__ == "__main__":
    # Run analytics first
    print("📊 Running guild analytics...")
    analytics = GuildAnalytics()
    if analytics.characters:
        analytics.export_analytics_report()
    
    # Generate dashboard
    generate_enhanced_dashboard()
