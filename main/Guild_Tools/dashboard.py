import csv
import os
import json
from datetime import datetime

def generate_html_dashboard(csv_file, output_file="dashboard.html", detailed_dir="detailed"):
    """Generate an interactive HTML dashboard from Player_data.csv"""
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Read data
    characters = []
    character_specs = {}  # Store spec icons
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            characters.append(row)
    
    # Load detailed character data and extract spec icons
    character_details = {}
    if os.path.exists(detailed_dir):
        for filename in os.listdir(detailed_dir):
            if filename.endswith('.md'):
                char_name = filename[:-3]  # Remove .md extension
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
    
    # Parse numeric values safely
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
    
    # WoW class colors (official Blizzard colors)
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
        'Demonhunter': '#A330C9'  # Alternative spelling
    }
    
    # WCL score colors
    def get_wcl_color(score):
        if score == 100: return '#e6cc80'  # Gold
        elif score >= 99: return '#e367a5'  # Pink
        elif score >= 95: return '#ff8000'  # Orange
        elif score >= 75: return '#a335ee'  # Epic purple
        elif score >= 50: return '#0070dd'  # Rare blue
        elif score >= 25: return '#1eff00'  # Uncommon green
        else: return '#808080'  # Grey
    
    # Create color arrays
    char_colors_class = [class_colors.get(cls, '#667eea') for cls in char_classes]
    
    char_mplus = []
    for c in characters:
        try:
            score = float(str(c['M+']).replace(',', ''))
            char_mplus.append(score)
        except:
            char_mplus.append(0)
    
    char_wcl = []
    char_colors_wcl = []
    for c in characters:
        try:
            score = float(str(c['WCL']).replace(',', ''))
            char_wcl.append(score)
            char_colors_wcl.append(get_wcl_color(score))
        except:
            char_wcl.append(0)
            char_colors_wcl.append('#808080')
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WoW Guild Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 20px;
        }}
        
        header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-card .label {{
            font-size: 0.85em;
            color: #999;
            margin-top: 5px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .chart-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .chart-card h2 {{
            margin-bottom: 20px;
            color: #333;
            font-size: 1.3em;
        }}
        
        .chart-container-large {{
            position: relative;
            height: 600px;
        }}
        
        .table-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover {{
            background: #f8f9ff;
        }}
        
        .performance-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .clickable {{
            cursor: pointer;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }}
        
        .clickable:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.6);
            backdrop-filter: blur(5px);
        }}
        
        .modal-content {{
            background-color: #fefefe;
            margin: 50px auto;
            padding: 0;
            border-radius: 15px;
            width: 90%;
            max-width: 900px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-height: 85vh;
            overflow-y: auto;
        }}
        
        .modal-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px 15px 0 0;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .modal-header h2 {{
            margin: 0;
            font-size: 1.8em;
        }}
        
        .modal-body {{
            padding: 30px;
            line-height: 1.8;
        }}
        
        .modal-body h2, .modal-body h3, .modal-body h4 {{
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        
        .modal-body h2 {{
            font-size: 1.8em;
            color: #667eea;
        }}
        
        .modal-body h3 {{
            font-size: 1.4em;
            color: #764ba2;
        }}
        
        .modal-body h4 {{
            font-size: 1.2em;
            color: #333;
        }}
        
        .modal-body p {{
            margin-bottom: 10px;
        }}
        
        .modal-body ul, .modal-body ol {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        
        .modal-body table {{
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .modal-body hr {{
            margin: 30px 0;
            border: none;
            border-top: 2px solid #eee;
        }}
        
        .close {{
            color: white;
            float: right;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
            transition: transform 0.2s;
        }}
        
        .close:hover {{
            transform: scale(1.2);
        }}
        
        footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚔️ Guild Performance Dashboard</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Members</h3>
                <div class="value">{total_chars}</div>
                <div class="label">Active Characters</div>
            </div>
            <div class="stat-card">
                <h3>Average ilvl</h3>
                <div class="value">{avg_ilvl:.1f}</div>
                <div class="label">Guild Average</div>
            </div>
            <div class="stat-card">
                <h3>Average M+ Score</h3>
                <div class="value">{avg_mplus:.1f}</div>
                <div class="label">Mythic Plus Rating</div>
            </div>
            <div class="stat-card">
                <h3>Average WCL</h3>
                <div class="value">{avg_wcl:.1f}</div>
                <div class="label">Raid Performance</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card" style="grid-column: 1 / -1;">
                <h2>📊 Item Level Distribution</h2>
                <div class="chart-container-large">
                    <canvas id="ilvlChart"></canvas>
                </div>
            </div>
            
            <div class="chart-card" style="grid-column: 1 / -1;">
                <h2>🏔️ M+ Score Distribution</h2>
                <div class="chart-container-large">
                    <canvas id="mplusChart"></canvas>
                </div>
            </div>
            
            <div class="chart-card" style="grid-column: 1 / -1;">
                <h2>📈 Warcraft Logs Performance</h2>
                <div class="chart-container-large">
                    <canvas id="wclChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="table-card">
            <h2>📋 Detailed Character List</h2>
            <table>
                <thead>
                    <tr>
                        <th>Character</th>
                        <th>Class</th>
                        <th>Spec</th>
                        <th>ilvl</th>
                        <th>M+ Tier</th>
                        <th>WCL</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add table rows with clickable character names and spec icons
    for char in characters:
        char_name = char['ID']
        has_details = char_name in character_details
        spec_icon = character_specs.get(char_name, '')
        
        # Get M+ score for badge (using Raider.IO colors)
        try:
            mplus_val = float(str(char['M+']).replace(',', ''))
            if mplus_val >= 3000: mplus_color = '#FFA500'
            elif mplus_val >= 2750: mplus_color = '#FF8000'
            elif mplus_val >= 2500: mplus_color = '#FF6060'
            elif mplus_val >= 2250: mplus_color = '#C41E3A'
            elif mplus_val >= 2000: mplus_color = '#E268A8'
            elif mplus_val >= 1750: mplus_color = '#A335EE'
            elif mplus_val >= 1500: mplus_color = '#8788EE'
            elif mplus_val >= 1250: mplus_color = '#0070DD'
            elif mplus_val >= 1000: mplus_color = '#1EFF00'
            elif mplus_val >= 750: mplus_color = '#71D5FF'
            else: mplus_color = '#808080'
            mplus_badge = f'<span class="performance-badge" style="background: {mplus_color}; color: white;">{mplus_val:.0f}</span>'
        except:
            mplus_badge = '<span class="performance-badge" style="background: #808080; color: white;">N/A</span>'
        
        # Get WCL score for badge
        try:
            wcl_val = float(str(char['WCL']).replace(',', ''))
            wcl_color = get_wcl_color(wcl_val)
            wcl_badge = f'<span class="performance-badge" style="background: {wcl_color}; color: white;">{wcl_val:.1f}</span>'
        except:
            wcl_badge = '<span class="performance-badge" style="background: #808080; color: white;">N/A</span>'
        
        # Make name clickable if details exist
        name_display = f'<a href="#" class="clickable" onclick="showCharacterDetails(\'{char_name}\'); return false;">{char_name}</a>' if has_details else f'<strong>{char_name}</strong>'
        
        # Add spec icon to spec column
        spec_display = char['Spec']
        if spec_icon:
            spec_display = f'<img src="{spec_icon}" alt="spec" style="width: 24px; height: 24px; vertical-align: middle; margin-right: 6px; border-radius: 4px; border: 2px solid #667eea;" onerror="this.style.display=\'none\'"> {char["Spec"]}'
        
        html += f"""
                    <tr>
                        <td>{name_display}</td>
                        <td>{char['Class']}</td>
                        <td>{spec_display}</td>
                        <td>{char['ilvl']}</td>
                        <td>{mplus_badge}</td>
                        <td>{wcl_badge}</td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <!-- Modal for character details -->
        <div id="characterModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <span class="close" onclick="closeModal()">&times;</span>
                    <h2 id="modalTitle">Character Details</h2>
                </div>
                <div class="modal-body" id="modalBody">
                    <!-- Content will be inserted here -->
                </div>
            </div>
        </div>
        
        <footer>
            <p>두부킴의 유기견들</p>
        </footer>
    </div>
    
    <script>
        // Store character details
        const characterDetails = {json.dumps(character_details)};
        
        // Modal functions
        function showCharacterDetails(charName) {{
            const modal = document.getElementById('characterModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalBody = document.getElementById('modalBody');
            
            if (characterDetails[charName]) {{
                modalTitle.textContent = charName;
                
                // Convert markdown to HTML
                const content = characterDetails[charName];
                const lines = content.split('\\n');
                let html = '';
                let inTable = false;
                let tableRows = [];
                
                let isEquipmentSection = false;
                let specIcon = '';
                
                for (let i = 0; i < lines.length; i++) {{
                    let line = lines[i];
                    
                    // Extract and SKIP the SPEC_ICON line completely
                    if (line.startsWith('**SPEC_ICON:')) {{
                        specIcon = line.replace('**SPEC_ICON:', '').replace('**', '').trim();
                        continue; // Don't process this line at all
                    }}
                    
                    // Check if we're in equipment section
                    if (line.includes('## ⚔️ Equipment')) {{
                        isEquipmentSection = true;
                    }} else if (line.startsWith('##')) {{
                        isEquipmentSection = false;
                    }}
                    
                    if (line.trim().startsWith('|')) {{
                        if (!inTable) {{
                            inTable = true;
                            tableRows = [];
                        }}
                        tableRows.push(line);
                        continue;
                    }} else if (inTable) {{
                        html += processTable(tableRows, isEquipmentSection);
                        inTable = false;
                        tableRows = [];
                    }}
                    
                    if (line.startsWith('# ')) {{
                        html += `<h2>${{line.substring(2)}}</h2>`;
                    }} else if (line.startsWith('## ')) {{
                        html += `<h3>${{line.substring(3)}}</h3>`;
                    }} else if (line.startsWith('### ')) {{
                        html += `<h4>${{line.substring(4)}}</h4>`;
                    }} else if (line.trim() === '---') {{
                        html += '<hr>';
                    }} else if (line.trim() === '') {{
                        html += '<br>';
                    }} else {{
                        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                        line = line.replace(/\*(.+?)\*/g, '<em>$1</em>');
                        
                        // Add spec icon if this is the class/role line and we have an icon
                        if (specIcon && line.includes('|') && (line.includes('Tank') || line.includes('Healer') || line.includes('Melee') || line.includes('Ranged'))) {{
                            line = `<img src="${{specIcon}}" alt="spec" style="width: 24px; height: 24px; vertical-align: middle; margin-right: 8px; border-radius: 4px; border: 2px solid #667eea;" onerror="this.style.display='none'"> ` + line;
                        }}
                        
                        html += `<p>${{line}}</p>`;
                    }}
                }}
                
                if (inTable) {{
                    html += processTable(tableRows, isEquipmentSection);
                }}
                
                modalBody.innerHTML = html;
                modal.style.display = 'block';
            }}
        }}
        
        function processTable(rows, isEquipmentTable = false) {{
            if (rows.length === 0) return '';
            
            let html = '<table style="width:100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">';
            
            for (let i = 0; i < rows.length; i++) {{
                const cells = rows[i].split('|').filter(cell => cell.trim());
                
                if (cells[0] && cells[0].includes('---')) continue;
                
                if (i === 0) {{
                    html += '<thead><tr>';
                    cells.forEach((cell, idx) => {{
                        // Skip the Icon column header in equipment tables
                        if (!(isEquipmentTable && idx === 3 && cell.trim() === 'Icon')) {{
                            html += `<th style="background: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600;">${{cell.trim()}}</th>`;
                        }}
                    }});
                    html += '</tr></thead><tbody>';
                }} else {{
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    cells.forEach((cell, index) => {{
                        // For equipment tables
                        if (isEquipmentTable) {{
                            if (index === 1 && cells.length >= 4) {{
                                // This is the item name column, add icon
                                const iconCell = cells[3].trim();
                                if (iconCell.startsWith('ICON:')) {{
                                    const iconUrl = iconCell.substring(5); // Remove 'ICON:' prefix
                                    if (iconUrl && iconUrl.startsWith('http')) {{
                                        html += `<td style="padding: 12px;"><img src="${{iconUrl}}" alt="icon" style="width: 32px; height: 32px; vertical-align: middle; margin-right: 8px; border-radius: 4px; border: 2px solid #667eea;" onerror="this.style.display='none'"> ${{cell.trim()}}</td>`;
                                    }} else {{
                                        html += `<td style="padding: 12px;">${{cell.trim()}}</td>`;
                                    }}
                                }} else {{
                                    html += `<td style="padding: 12px;">${{cell.trim()}}</td>`;
                                }}
                            }} else if (index !== 3) {{
                                // Skip the Icon URL column (index 3)
                                html += `<td style="padding: 12px;">${{cell.trim()}}</td>`;
                            }}
                        }} else {{
                            html += `<td style="padding: 12px;">${{cell.trim()}}</td>`;
                        }}
                    }});
                    html += '</tr>';
                }}
            }}
            
            html += '</tbody></table>';
            return html;
        }}
        
        function closeModal() {{
            document.getElementById('characterModal').style.display = 'none';
        }}
        
        window.onclick = function(event) {{
            const modal = document.getElementById('characterModal');
            if (event.target == modal) {{
                modal.style.display = 'none';
            }}
        }}
        
        // Chart background plugin (lighter grey)
        const lighterBgPlugin = {{
            beforeDraw: (chart) => {{
                const ctx = chart.ctx;
                ctx.save();
                ctx.fillStyle = '#F5F5F5';
                ctx.fillRect(0, 0, chart.width, chart.height);
                ctx.restore();
            }}
        }};
        
        // Item Level Chart
        new Chart(document.getElementById('ilvlChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(char_names)},
                datasets: [{{
                    label: 'Item Level',
                    data: {json.dumps(char_ilvls)},
                    backgroundColor: {json.dumps(char_colors_class)},
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            font: {{
                                size: 11
                            }},
                            color: '#000000'
                        }},
                        grid: {{
                            color: '#CCCCCC'
                        }}
                    }},
                    y: {{
                        min: 700,
                        max: 730,
                        ticks: {{
                            stepSize: 10,
                            color: '#000000'
                        }},
                        grid: {{
                            color: '#CCCCCC'
                        }}
                    }}
                }},
                layout: {{
                    padding: 10
                }}
            }},
            plugins: [lighterBgPlugin]
        }});
        
        // M+ Score Chart (with class colors)
        new Chart(document.getElementById('mplusChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(char_names)},
                datasets: [{{
                    label: 'M+ Score',
                    data: {json.dumps(char_mplus)},
                    backgroundColor: {json.dumps(char_colors_class)},
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            font: {{
                                size: 11
                            }},
                            color: '#000000'
                        }},
                        grid: {{
                            color: '#CCCCCC'
                        }}
                    }},
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            color: '#000000'
                        }},
                        grid: {{
                            color: '#CCCCCC'
                        }}
                    }}
                }},
                layout: {{
                    padding: 10
                }}
            }},
            plugins: [lighterBgPlugin]
        }});
        
        // WCL Score Chart (with class colors)
        new Chart(document.getElementById('wclChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(char_names)},
                datasets: [{{
                    label: 'WCL Score',
                    data: {json.dumps(char_wcl)},
                    backgroundColor: {json.dumps(char_colors_class)},
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            font: {{
                                size: 11
                            }},
                            color: '#000000'
                        }},
                        grid: {{
                            color: '#CCCCCC'
                        }}
                    }},
                    y: {{
                        min: 0,
                        max: 100,
                        ticks: {{
                            stepSize: 10,
                            color: '#000000'
                        }},
                        grid: {{
                            color: '#CCCCCC'
                        }}
                    }}
                }},
                layout: {{
                    padding: 10
                }}
            }},
            plugins: [lighterBgPlugin]
        }});
    </script>
</body>
</html>
    """
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"📊 Open it in your browser to view!")

if __name__ == "__main__":
    generate_html_dashboard("logs/Player_data.csv")
