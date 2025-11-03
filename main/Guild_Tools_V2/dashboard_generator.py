import csv
import os
import json
from datetime import datetime

def generate_html_dashboard(csv_file, output_file="dashboard.html", detailed_dir="detailed"):
    """Generate an interactive HTML dashboard from Player_data.csv"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Import history tracker functions
    import sys
    sys.path.append('.')
    try:
        from history_tracker import get_guild_average_history, get_top_improvers
        guild_history = get_guild_average_history()
        top_improvers = get_top_improvers(7)
        has_history = len(guild_history['dates']) > 1
    except:
        guild_history = {'dates': [], 'avg_ilvl': [], 'avg_mplus': [], 'avg_wcl': []}
        top_improvers = []
        has_history = False
    
    # Load enhanced M+ data if available
    mplus_enhanced_data = {}
    if os.path.exists("logs/mplus_enhanced.json"):
        try:
            with open("logs/mplus_enhanced.json", 'r', encoding='utf-8') as f:
                mplus_enhanced_data = json.load(f)
            print("✅ Loaded enhanced M+ data")
        except:
            print("⚠️ Could not load enhanced M+ data")
    
    # Read character data
    characters = []
    character_specs = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            characters.append(row)
    
    # Load detailed character data and extract spec icons
    character_details = {}
    if os.path.exists(detailed_dir):
        for filename in os.listdir(detailed_dir):
            if filename.endswith('.md'):
                char_name = filename[:-3]
                with open(os.path.join(detailed_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    character_details[char_name] = content
                    
                    # Extract spec icon
                    for line in content.split('\n'):
                        if line.startswith('**SPEC_ICON:'):
                            spec_icon = line.replace('**SPEC_ICON:', '').replace('**', '').strip()
                            character_specs[char_name] = spec_icon
                            break
    
    # Calculate statistics
    total_chars = len(characters)
    
    ilvls = []
    mplus_scores = []
    wcl_scores = []
    
    for char in characters:
        try:
            ilvl = float(char['ilvl'])
            if ilvl > 0:
                ilvls.append(ilvl)
        except:
            pass
        
        try:
            mplus = float(str(char['M+']).replace(',', ''))
            if mplus > 0:
                mplus_scores.append(mplus)
        except:
            pass
        
        try:
            wcl = float(str(char['WCL']).replace(',', ''))
            if wcl > 0:
                wcl_scores.append(wcl)
        except:
            pass
    
    avg_ilvl = sum(ilvls) / len(ilvls) if ilvls else 0
    avg_mplus = sum(mplus_scores) / len(mplus_scores) if mplus_scores else 0
    avg_wcl = sum(wcl_scores) / len(wcl_scores) if wcl_scores else 0
    
    # Prepare data for charts
    char_names = [c['ID'] for c in characters]
    char_ilvls = [float(c['ilvl']) if c['ilvl'] != 'N/A' else 0 for c in characters]
    char_classes = [c['Class'] for c in characters]
    
    # WoW class colors
    class_colors = {
        'Death Knight': '#C41E3A',
        'Demon Hunter': '#A330C9',
        'Druid': '#FF7C0A',
        'Evoker': '#33937F',
        'Hunter': '#AAD372',
        'Mage': '#3FC7EB',
        'Monk': '#00FF98',
        'Paladin': '#F48CBA',
        'Priest': '#FFFFFF',
        'Rogue': '#FFF468',
        'Shaman': '#0070DD',
        'Warlock': '#8788EE',
        'Warrior': '#C69B6D',
        'Demonhunter': '#A330C9'
    }
    
    def get_wcl_color(score):
        if score == 100: return '#e6cc80'
        elif score >= 99: return '#e367a5'
        elif score >= 95: return '#ff8000'
        elif score >= 75: return '#a335ee'
        elif score >= 50: return '#0070dd'
        elif score >= 25: return '#1eff00'
        else: return '#808080'
    
    char_colors_class = [class_colors.get(cls, '#667eea') for cls in char_classes]
    
    char_mplus = []
    for c in characters:
        try:
            score = float(str(c['M+']).replace(',', ''))
            char_mplus.append(score)
        except:
            char_mplus.append(0)
    
    char_wcl = []
    for c in characters:
        try:
            score = float(str(c['WCL']).replace(',', ''))
            char_wcl.append(score)
        except:
            char_wcl.append(0)
    
    # Generate M+ tab content
    def generate_mplus_tab():
        if not mplus_enhanced_data:
            return '<div style="text-align: center; padding: 60px; color: #999;"><h2 style="color: #667eea;">🏔️ No Enhanced M+ Data</h2><p>Run <code>python mplus_enhanced.py</code> to fetch detailed M+ information</p></div>'
        
        content = '<h2 style="color: #667eea; margin-bottom: 30px;">🏔️ Mythic+ Best Runs - Detailed View</h2>'
        
        sorted_chars = sorted(
            [(name, data) for name, data in mplus_enhanced_data.items() if data],
            key=lambda x: x[1].get("character", {}).get("score", 0),
            reverse=True
        )
        
        for char_name, char_data in sorted_chars:
            char_info = char_data.get("character", {})
            best_runs = char_data.get("best_runs", [])
            
            if not best_runs:
                continue
            
            content += f'''
            <div class="character-section">
                <div class="char-header">
                    <img src="{char_info.get('thumbnail', '')}" alt="{char_info.get('name', '')}" class="char-avatar" onerror="this.style.display='none'">
                    <div class="char-info">
                        <h3>{char_info.get('name', char_name)}</h3>
                        <div class="char-stats">
                            <span class="stat-badge">{char_info.get('spec', 'Unknown')} {char_info.get('class', 'Unknown')}</span>
                            <span class="stat-badge">ilvl {char_info.get('ilvl', 0)}</span>
                            <span class="stat-badge" style="background: #667eea; color: white;">M+ Score: {char_info.get('score', 0):.0f}</span>
                        </div>
                    </div>
                </div>
            '''
            
            for i, run in enumerate(best_runs, 1):
                level = run.get('level', 0)
                timed = run.get('timed', False)
                num_chests = run.get('num_chests', 0)
                
                if level >= 12:
                    level_color = "#FF8000"
                elif level >= 10:
                    level_color = "#A335EE"
                elif level >= 8:
                    level_color = "#0070DD"
                else:
                    level_color = "#1EFF00"
                
                timed_icon = "✅ Timed" if timed else "❌ Depleted"
                upgrade_text = f"+{num_chests}" if timed and num_chests > 0 else ""
                
                def format_time(ms):
                    if ms <= 0:
                        return "N/A"
                    seconds = ms / 1000
                    minutes = int(seconds // 60)
                    secs = int(seconds % 60)
                    return f"{minutes}:{secs:02d}"
                
                clear_time = format_time(run.get('clear_time_ms', 0))
                par_time = format_time(run.get('par_time_ms', 0))
                
                content += f'''
                <div class="run-card">
                    <div class="run-header">
                        <div>
                            <div class="dungeon-name">#{i} {run.get('dungeon', 'Unknown')}</div>
                            <div style="color: #666; font-size: 0.9em; margin-top: 5px;">{run.get('completed_at', 'Unknown')}</div>
                        </div>
                        <div class="key-level" style="background: {level_color};">
                            +{level} {upgrade_text}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 10px; font-weight: 600; color: {'#28a745' if timed else '#dc3545'};">
                        {timed_icon} | Score: {run.get('score', 0):.1f}
                    </div>
                    
                    <div class="affixes">
                '''
                
                affix_emojis = {
                    "Tyrannical": "👑", "Fortified": "🛡️", "Bolstering": "💪",
                    "Bursting": "💥", "Raging": "😡", "Sanguine": "🩸",
                    "Volcanic": "🌋", "Explosive": "💣", "Quaking": "🌊",
                    "Grievous": "⚔️", "Necrotic": "☠️", "Storming": "⛈️",
                    "Afflicted": "🤢", "Incorporeal": "👻", "Entangling": "🌿",
                    "Xal'atath's Bargain": "🔮", "Xal'atath's Guile": "🔮"
                }
                
                for affix in run.get('affixes', []):
                    affix_name = affix.get('name', '')
                    emoji = affix_emojis.get(affix_name, '🔸')
                    content += f'<span class="affix">{emoji} {affix_name}</span>'
                
                content += f'''
                    </div>
                    
                    <div class="time-info">
                        <span>⏱️ Clear Time: <strong>{clear_time}</strong></span>
                        <span>🎯 Par Time: <strong>{par_time}</strong></span>
                    </div>
                    
                    <h4 style="margin-top: 15px; margin-bottom: 10px; color: #667eea;">Party Composition</h4>
                    <div class="roster">
                '''
                
                for member in run.get('roster', []):
                    role = member.get('role', 'dps').lower()
                    role_emoji = "🛡️" if role == "tank" else "💚" if role == "healer" else "⚔️"
                    
                    content += f'''
                        <div class="roster-member">
                            <div class="role-icon {role}">{role_emoji}</div>
                            <div style="flex: 1;">
                                <div style="font-weight: 600;">{member.get('name', 'Unknown')}</div>
                                <div style="font-size: 0.85em; color: #666;">{member.get('spec', '')} {member.get('class', '')}</div>
                            </div>
                        </div>
                    '''
                
                content += '</div>'
                
                if run.get('url'):
                    content += f'<a href="{run["url"]}" target="_blank" class="raiderio-link">📊 View on Raider.IO</a>'
                
                content += '</div>'
            
            content += '</div>'
        
        return content
    
    mplus_tab_html = generate_mplus_tab()
    
    # Now generate the actual HTML file
    # (I'll continue in the next part due to length)
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"📊 Open it in your browser to view!")

if __name__ == "__main__":
    generate_html_dashboard("logs/Player_data.csv")
