import csv
import os
import json
from datetime import datetime

def generate_html_dashboard(csv_file, output_file="dashboard.html", detailed_dir="detailed"):
    """Generate complete interactive dashboard"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🎨 Generating dashboard...")
    
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
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        characters = list(csv.DictReader(f))
    
    if os.path.exists(detailed_dir):
        for fname in os.listdir(detailed_dir):
            if fname.endswith('.md'):
                name = fname[:-3]
                with open(os.path.join(detailed_dir, fname), 'r') as f:
                    content = f.read()
                    character_details[name] = content
                    for line in content.split('\n'):
                        if line.startswith('**SPEC_ICON:'):
                            character_specs[name] = line.replace('**SPEC_ICON:', '').replace('**', '').strip()
                            break
    
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
        'Death Knight':'#C41E3A','Demon Hunter':'#A330C9','Druid':'#FF7C0A',
        'Evoker':'#33937F','Hunter':'#AAD372','Mage':'#3FC7EB',
        'Monk':'#00FF98','Paladin':'#F48CBA','Priest':'#FFFFFF',
        'Rogue':'#FFF468','Shaman':'#0070DD','Warlock':'#8788EE',
        'Warrior':'#C69B6D','Demonhunter':'#A330C9'
    }
    colors = [class_colors.get(c,'#667eea') for c in classes]
    
    def wcl_color(s):
        if s==100: return '#e6cc80'
        elif s>=99: return '#e367a5'
        elif s>=95: return '#ff8000'
        elif s>=75: return '#a335ee'
        elif s>=50: return '#0070dd'
        elif s>=25: return '#1eff00'
        return '#808080'
    
    # Generate HTML - keeping it simpler and complete
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Guild Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}}
.container{{max-width:1400px;margin:0 auto}}
header{{text-align:center;color:#fff;margin-bottom:40px;padding:20px}}
h1{{font-size:3em}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}}
.stat-card{{background:#fff;border-radius:15px;padding:25px;box-shadow:0 10px 30px rgba(0,0,0,.2)}}
.value{{font-size:2.5em;font-weight:bold;color:#667eea}}
.tab-container{{background:#fff;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.2);margin-bottom:40px;overflow:hidden}}
.tab-nav{{display:flex;background:#f0f0f0;border-bottom:2px solid #667eea}}
.tab-btn{{flex:1;padding:20px;background:none;border:none;cursor:pointer;font-size:1.1em;font-weight:600;color:#666}}
.tab-btn:hover{{background:rgba(102,126,234,.1)}}
.tab-btn.active{{background:#fff;color:#667eea;border-bottom:3px solid #667eea}}
.tab-content{{display:none;padding:30px}}
.tab-content.active{{display:block}}
.chart-container{{position:relative;height:600px}}
table{{width:100%;border-collapse:collapse}}
th{{background:#667eea;color:#fff;padding:12px;text-align:left}}
td{{padding:12px;border-bottom:1px solid #eee}}
tr:hover{{background:#f8f9ff}}
.clickable{{cursor:pointer;color:#667eea;font-weight:600;text-decoration:none}}
.clickable:hover{{text-decoration:underline}}
.badge{{display:inline-block;padding:4px 12px;border-radius:12px;font-size:.85em;font-weight:600}}
.modal{{display:none;position:fixed;z-index:1000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.6)}}
.modal-content{{background:#fff;margin:50px auto;padding:0;border-radius:15px;width:90%;max-width:900px;max-height:85vh;overflow-y:auto}}
.modal-header{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:25px;border-radius:15px 15px 0 0;position:sticky;top:0}}
.modal-body{{padding:30px}}
.close{{color:#fff;float:right;font-size:32px;font-weight:bold;cursor:pointer}}
.char-section{{background:#f8f9fa;border-radius:15px;padding:25px;margin-bottom:30px;border:2px solid #e0e0e0}}
.char-header{{display:flex;align-items:center;margin-bottom:20px;padding-bottom:15px;border-bottom:2px solid #667eea}}
.char-avatar{{width:80px;height:80px;border-radius:10px;margin-right:20px;border:3px solid #667eea}}
.run-card{{background:#fff;border-radius:10px;padding:20px;margin-bottom:15px;border-left:4px solid #667eea}}
.run-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}}
.key-level{{font-size:1.5em;font-weight:bold;padding:8px 20px;border-radius:8px;color:#fff}}
.affixes{{display:flex;gap:10px;margin:15px 0;flex-wrap:wrap}}
.affix{{background:#667eea;color:#fff;padding:6px 12px;border-radius:6px;font-size:.85em}}
.roster{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-top:15px}}
.roster-member{{background:#f8f9fa;padding:12px;border-radius:8px;display:flex;align-items:center;gap:12px;border:1px solid #e0e0e0}}
.role-icon{{width:35px;height:35px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.2em}}
.tank{{background:#C41E3A;color:#fff}}
.healer{{background:#1EFF00;color:#fff}}
.dps{{background:#667eea;color:#fff}}
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
</div>
<div id="overview" class="tab-content active">
<h2>Guild Progress Trends</h2>
<div class="chart-container"><canvas id="trendChart"></canvas></div>
<h2 style="margin-top:40px">Top Improvers</h2>
<table style="margin-top:20px"><thead><tr><th>Rank</th><th>Character</th><th>Class</th><th>ilvl</th><th>M+</th><th>WCL</th></tr></thead><tbody>
"""
    
    if top_improvers:
        for i,p in enumerate(top_improvers[:10],1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            html_content += f'<tr><td>{medal}</td><td><b>{p["name"]}</b></td><td>{p["spec"]} {p["class"]}</td><td style="color:#28a745">+{p["ilvl_gain"]:.1f}</td><td style="color:#28a745">+{p["mplus_gain"]:.0f}</td><td style="color:#28a745">+{p["wcl_gain"]:.1f}</td></tr>'
    else:
        html_content += '<tr><td colspan="6" style="text-align:center;padding:20px">No data yet</td></tr>'
    
    html_content += """</tbody></table></div>
<div id="roster" class="tab-content">
<h2>Character Roster</h2>
<table style="margin-top:20px"><thead><tr><th>Character</th><th>Class</th><th>Spec</th><th>ilvl</th><th>M+</th><th>WCL</th></tr></thead><tbody>
"""
    
    for c in characters:
        name = c['ID']
        has_detail = name in character_details
        spec_icon = character_specs.get(name,'')
        spec_disp = f'<img src="{spec_icon}" style="width:24px;height:24px;vertical-align:middle;margin-right:6px;border-radius:4px" onerror="this.style.display=\'none\'"> {c["Spec"]}' if spec_icon else c['Spec']
        name_disp = f'<a href="#" class="clickable" onclick="showChar(\'{name}\');return false">{name}</a>' if has_detail else f'<b>{name}</b>'
        
        try:
            mp = float(str(c['M+']).replace(',',''))
            mp_badge = f'<span class="badge" style="background:#667eea;color:#fff">{mp:.0f}</span>'
        except:
            mp_badge = '<span class="badge" style="background:#808080;color:#fff">N/A</span>'
        
        try:
            wc = float(str(c['WCL']).replace(',',''))
            wc_col = wcl_color(wc)
            wc_badge = f'<span class="badge" style="background:{wc_col};color:#fff">{wc:.1f}</span>'
        except:
            wc_badge = '<span class="badge" style="background:#808080;color:#fff">N/A</span>'
        
        html_content += f'<tr><td>{name_disp}</td><td>{c["Class"]}</td><td>{spec_disp}</td><td>{c["ilvl"]}</td><td>{mp_badge}</td><td>{wc_badge}</td></tr>'
    
    html_content += """</tbody></table></div>
<div id="charts" class="tab-content">
<h2>Item Level</h2><div class="chart-container"><canvas id="ilvlChart"></canvas></div>
<h2 style="margin-top:40px">M+ Score</h2><div class="chart-container"><canvas id="mplusChart"></canvas></div>
<h2 style="margin-top:40px">WCL</h2><div class="chart-container"><canvas id="wclChart"></canvas></div>
</div>
<div id="mplus" class="tab-content">
"""
    
    if mplus_data:
        html_content += '<h2 style="margin-bottom:30px">Mythic+ Best Runs</h2>'
        sorted_m = sorted([(n,d) for n,d in mplus_data.items() if d], key=lambda x:x[1].get("character",{}).get("score",0), reverse=True)
        
        for name,data in sorted_m:
            ci = data.get("character",{})
            runs = data.get("best_runs",[])
            if not runs: continue
            
            html_content += f'<div class="char-section"><div class="char-header"><img src="{ci.get("thumbnail","")}" class="char-avatar" onerror="this.style.display=\'none\'"><div><h3>{ci.get("name",name)}</h3><div style="display:flex;gap:15px;margin-top:10px"><span class="badge">{ci.get("spec","")} {ci.get("class","")}</span><span class="badge">ilvl {ci.get("ilvl",0)}</span><span class="badge" style="background:#667eea;color:#fff">M+ {ci.get("score",0):.0f}</span></div></div></div>'
            
            for i,run in enumerate(runs,1):
                lv = run.get('level',0)
                timed = run.get('timed',False)
                chests = run.get('num_chests',0)
                lv_col = "#FF8000" if lv>=12 else "#A335EE" if lv>=10 else "#0070DD" if lv>=8 else "#1EFF00"
                up_txt = f"+{chests}" if timed and chests>0 else ""
                
                def fmt(ms):
                    if ms<=0: return "N/A"
                    s=ms/1000
                    return f"{int(s//60)}:{int(s%60):02d}"
                
                html_content += f'<div class="run-card"><div class="run-header"><div><div style="font-size:1.3em;font-weight:600">#{i} {run.get("dungeon","")}</div><div style="color:#666;font-size:.9em">{run.get("completed_at","")}</div></div><div class="key-level" style="background:{lv_col}">+{lv} {up_txt}</div></div><div style="margin-bottom:10px;font-weight:600;color:{"#28a745" if timed else "#dc3545"}">{"✅ Timed" if timed else "❌ Depleted"} | Score: {run.get("score",0):.1f}</div><div class="affixes">'
                
                aff_emoji = {"Tyrannical":"👑","Fortified":"🛡️","Bolstering":"💪","Bursting":"💥","Raging":"😡","Sanguine":"🩸","Volcanic":"🌋","Explosive":"💣","Quaking":"🌊","Grievous":"⚔️","Necrotic":"☠️","Storming":"⛈️","Afflicted":"🤢","Incorporeal":"👻","Entangling":"🌿","Xal'atath's Bargain":"🔮","Xal'atath's Guile":"🔮"}
                
                for aff in run.get('affixes',[]):
                    html_content += f'<span class="affix">{aff_emoji.get(aff.get("name",""),"🔸")} {aff.get("name","")}</span>'
                
                html_content += f'</div><div style="display:flex;gap:20px;margin:15px 0"><span>⏱️ {fmt(run.get("clear_time_ms",0))}</span><span>🎯 {fmt(run.get("par_time_ms",0))}</span></div><h4 style="color:#667eea">Party</h4><div class="roster">'
                
                for mem in run.get('roster',[]):
                    role = mem.get('role','dps').lower()
                    emoji = "🛡️" if role=="tank" else "💚" if role=="healer" else "⚔️"
                    html_content += f'<div class="roster-member"><div class="role-icon {role}">{emoji}</div><div><div style="font-weight:600">{mem.get("name","")}</div><div style="font-size:.85em;color:#666">{mem.get("spec","")} {mem.get("class","")}</div></div></div>'
                
                if run.get('url'):
                    html_content += f'<a href="{run["url"]}" target="_blank" style="display:inline-block;margin-top:10px;padding:10px 20px;background:#667eea;color:#fff;text-decoration:none;border-radius:8px">View on Raider.IO</a>'
                
                html_content += '</div></div>'
            
            html_content += '</div>'
    else:
        html_content += '<div style="text-align:center;padding:60px"><h2>No M+ Data</h2><p>Run python mplus_enhanced.py</p></div>'
    
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
function switchTab(e,t){{document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));document.querySelectorAll('.tab-btn').forEach(el=>el.classList.remove('active'));document.getElementById(t).classList.add('active');e.currentTarget.classList.add('active')}}
function showChar(n){{const m=document.getElementById('modal');document.getElementById('modalTitle').textContent=n;if(details[n]){{let c=details[n],lines=c.split('\\n'),html='',inT=false,rows=[],isEq=false,specIcon='';for(let line of lines){{if(line.startsWith('**SPEC_ICON:')){{specIcon=line.replace('**SPEC_ICON:','').replace('**','').trim();continue}}if(line.includes('## ⚔️ Equipment'))isEq=true;else if(line.startsWith('##'))isEq=false;if(line.trim().startsWith('|')){{if(!inT){{inT=true;rows=[]}}rows.push(line);continue}}else if(inT){{html+=procTable(rows,isEq);inT=false;rows=[]}}if(line.startsWith('# '))html+=`<h2>${{line.substring(2)}}</h2>`;else if(line.startsWith('## '))html+=`<h3>${{line.substring(3)}}</h3>`;else if(line.startsWith('### '))html+=`<h4>${{line.substring(4)}}</h4>`;else if(line.trim()==='---')html+='<hr>';else if(line.trim()==='')html+='<br>';else{{line=line.replace(/\\*\\*(.+?)\\*\\*/g,'<strong>$1</strong>').replace(/\\*(.+?)\\*/g,'<em>$1</em>');if(specIcon&&line.includes('|')&&(line.includes('Tank')||line.includes('Healer')||line.includes('Melee')||line.includes('Ranged')))line=`<img src="${{specIcon}}" style="width:24px;height:24px;vertical-align:middle;margin-right:8px;border-radius:4px;border:2px solid #667eea" onerror="this.style.display='none'"> `+line;html+=`<p>${{line}}</p>`}}}}if(inT)html+=procTable(rows,isEq);document.getElementById('modalBody').innerHTML=html;m.style.display='block'}}}}
function procTable(rows,isEq){{if(!rows.length)return '';let h='<table style="width:100%;border-collapse:collapse;margin:20px 0">';for(let i=0;i<rows.length;i++){{const cells=rows[i].split('|').filter(c=>c.trim());if(cells[0]&&cells[0].includes('---'))continue;if(i===0){{h+='<thead><tr>';cells.forEach((c,idx)=>{{if(!(isEq&&idx===3&&c.trim()==='Icon'))h+=`<th style="background:#667eea;color:#fff;padding:12px">${{c.trim()}}</th>`}});h+='</tr></thead><tbody>'}}else{{h+='<tr>';cells.forEach((c,idx)=>{{if(isEq){{if(idx===1&&cells.length>=4){{const ic=cells[3].trim();if(ic.startsWith('ICON:')){{const url=ic.substring(5);if(url&&url.startsWith('http'))h+=`<td style="padding:12px"><img src="${{url}}" style="width:32px;height:32px;vertical-align:middle;margin-right:8px;border-radius:4px;border:2px solid #667eea" onerror="this.style.display='none'"> ${{c.trim()}}</td>`;else h+=`<td style="padding:12px">${{c.trim()}}</td>`}}else h+=`<td style="padding:12px">${{c.trim()}}</td>`}}else if(idx!==3)h+=`<td style="padding:12px">${{c.trim()}}</td>`}}else h+=`<td style="padding:12px">${{c.trim()}}</td>`}});h+='</tr>'}}}}return h+'</tbody></table>'}}
function closeModal(){{document.getElementById('modal').style.display='none'}}
window.onclick=e=>{{if(e.target==document.getElementById('modal'))closeModal()}}
const bg={{beforeDraw:c=>{{const x=c.ctx;x.save();x.fillStyle='#F5F5F5';x.fillRect(0,0,c.width,c.height);x.restore()}}}};
new Chart(document.getElementById('trendChart'),{{type:'line',data:{{labels:{json.dumps(guild_history['dates'])},datasets:[{{label:'ilvl',data:{json.dumps(guild_history['avg_ilvl'])},borderColor:'#667eea',tension:.4,yAxisID:'y1'}},{{label:'M+',data:{json.dumps(guild_history['avg_mplus'])},borderColor:'#FF6B6B',tension:.4,yAxisID:'y2'}},{{label:'WCL',data:{json.dumps(guild_history['avg_wcl'])},borderColor:'#4ECDC4',tension:.4,yAxisID:'y3'}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y1:{{type:'linear',position:'left',title:{{display:true,text:'ilvl',color:'#667eea'}},ticks:{{color:'#667eea'}}}},y2:{{type:'linear',position:'right',title:{{display:true,text:'M+',color:'#FF6B6B'}},ticks:{{color:'#FF6B6B'}},grid:{{display:false}}}},y3:{{type:'linear',position:'right',title:{{display:true,text:'WCL',color:'#4ECDC4'}},ticks:{{color:'#4ECDC4'}},grid:{{display:false}}}}}}}},plugins:[bg]}});
new Chart(document.getElementById('ilvlChart'),{{type:'bar',data:{{labels:{json.dumps(names)},datasets:[{{data:{json.dumps(ilvl_data)},backgroundColor:{json.dumps(colors)}}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{x:{{ticks:{{autoSkip:false,maxRotation:0}}}}}}}},plugins:[bg]}});
new Chart(document.getElementById('mplusChart'),{{type:'bar',data:{{labels:{json.dumps(names)},datasets:[{{data:{json.dumps(mplus_data_chart)},backgroundColor:{json.dumps(colors)}}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{x:{{ticks:{{autoSkip:false,maxRotation:0}}}}}}}},plugins:[bg]}});
new Chart(document.getElementById('wclChart'),{{type:'bar',data:{{labels:{json.dumps(names)},datasets:[{{data:{json.dumps(wcl_data)},backgroundColor:{json.dumps(colors)}}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{x:{{ticks:{{autoSkip:false,maxRotation:0}}}},y:{{min:0,max:100}}}}}},plugins:[bg]}});
</script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"   - 4 tabs (Overview, Roster, Charts, M+ Details)")
    print(f"   - Click character names to see equipment")
    print(f"   - 3 separate Y-axes on trend chart")

if __name__ == "__main__":
    generate_html_dashboard("logs/Player_data.csv")
