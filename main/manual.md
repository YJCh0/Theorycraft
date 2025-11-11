# Guild Dashboard Generator - Documentation

## Overview
The dashboard generator creates an interactive HTML dashboard displaying WoW guild member statistics, including item levels, Mythic+ scores, and Warcraft Logs performance.

## File Structure

```
dashboard_generator.py          # Main file
├── Data Parsers                # Parse markdown files
│   ├── parse_wcl_from_markdown()
│   ├── parse_trinkets_from_markdown()
│   └── parse_equipment_from_markdown()
├── Utilities                   # Helper functions
│   ├── get_rio_color()
│   ├── wcl_color()
│   └── check_missing_buffs()
└── HTML Generator              # Build dashboard
    └── generate_html_dashboard()
```

## Key Components

### 1. Data Parsers

#### `parse_wcl_from_markdown(content)`
**Purpose**: Extracts Warcraft Logs data from character markdown files

**Input**: String content of markdown file

**Output**: Dictionary with structure:
```python
{
    'has_logs': bool,
    'mythic': {
        'best_performance': float,
        'boss_rankings': [
            {
                'boss': str,
                'rank_percent': float,
                'best_amount': int,
                'total_kills': int,
                'rank_details': {
                    'partition': str,
                    'spec': str,
                    'overall': str,
                    'region': str,
                    'server': str
                },
                'trinkets': []
            }
        ]
    },
    'heroic': {...},
    'all_stars': []
}
```

#### `parse_trinkets_from_markdown(content)`
**Purpose**: Extracts equipped trinket information

**Output**: List of trinket dictionaries:
```python
[
    {
        'name': str,
        'ilvl': str,
        'upgrade': str,
        'icon': str  # URL
    }
]
```

### 2. Utility Functions

#### `get_rio_color(score)` & `wcl_color(s)`
**Purpose**: Return hex color codes based on performance scores
- Used for visual color-coding of badges and bars

#### `check_missing_buffs(characters)`
**Purpose**: Analyzes roster composition for raid buff coverage
**Returns**: Tuple of (present_buffs, missing_buffs)

### 3. HTML Generation

#### `generate_html_dashboard(csv_file, output_file, detailed_dir)`
**Main function that orchestrates dashboard creation**

**Process Flow**:
1. Load data from CSV and markdown files
2. Calculate statistics (averages, totals)
3. Build HTML components:
   - Header with stats cards
   - Tab navigation
   - Overview tab (trends, top improvers)
   - Roster tab (sortable table)
   - Charts tab (ilvl, M+, WCL distributions)
   - M+ Details tab (recent runs)
   - Raiding tab (boss rankings)
4. Add JavaScript for interactivity
5. Write to HTML file

## Dashboard Tabs Explained

### Overview Tab
- **Guild Progress Trends**: Line chart showing historical averages
- **Top Improvers**: Table of characters with biggest gains (7 days)

### Roster Tab
- **Raid Buff Coverage**: Visual display of present/missing buffs
- **Character Table**: Sortable by name, ilvl, M+, WCL
- **Profile Links**: Armory, Raider.IO, Warcraft Logs

### Charts Tab
- Three bar charts showing distributions:
  - Item Level Distribution
  - M+ Score Distribution
  - WCL Performance Distribution

### M+ Details Tab
- **Per Character Sections**: Collapsible
  - Character info (spec, class, M+ score)
  - Recent runs (up to 5 shown)
  - Run details: dungeon, key level, time, affixes, party composition
  - **Trinkets**: Currently shows equipped (placeholder for run-specific)

### Raiding Tab
- **Per Character Sections**:
  - Performance badges (Mythic/Heroic)
  - Equipped raid trinkets
  - Boss rankings with progress bars
  - Detailed ranking tables (Overall, Region, Server)

## Data Flow Diagram

```
CSV File (Player_data.csv)
    ↓
Read Characters
    ↓
For each character:
    ├── Read detailed/{name}.md
    ├── Extract spec icon, server
    ├── Parse WCL data
    └── Parse trinkets
    ↓
Calculate Guild Stats
    ↓
Build HTML Components
    ├── Stats Cards
    ├── Tabs
    ├── Tables
    ├── Charts
    └── Modal
    ↓
Add JavaScript
    ├── Tab switching
    ├── Table sorting
    ├── Chart rendering
    └── Modal display
    ↓
Write dashboard.html
```

## JavaScript Components

### Tab Switching
```javascript
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Switch active tab
    });
});
```

### Table Sorting
```javascript
// Sorts roster by: name, ilvl, mplus, wcl
document.querySelectorAll('.sort-btn[data-sort]')
```

### Modal Display
```javascript
function showChar(name) {
    // Display character details in modal
    // Include: stats, equipment, trinkets, WCL rankings
}
```

### Charts (Chart.js)
- Trend Chart: Multi-axis line chart
- Distribution Charts: Bar charts with class colors

## Known Limitations & Future Improvements

### Current Limitations
1. **M+ Trinkets**: Shows equipped trinkets, not run-specific
   - **Future**: Integrate WCL API to fetch trinkets used in each run
2. **Modal Content**: Simplified character details
   - **Future**: Full equipment breakdown, talent builds
3. **Static Data**: No real-time updates
   - **Future**: Add refresh button with API calls

### Improvement Roadmap
1. **Phase 1**: Fix broken layouts, ensure all data displays
2. **Phase 2**: Add WCL API integration for run-specific trinkets
3. **Phase 3**: Add filtering (by role, class, spec)
4. **Phase 4**: Add export functionality (PDF, Excel)
5. **Phase 5**: Add real-time data refresh

## Troubleshooting

### Dashboard Shows Blank/Broken
- **Check**: All required files exist (CSV, markdown files, mplus_enhanced.json)
- **Check**: No syntax errors in generated HTML
- **Check**: Browser console for JavaScript errors

### Charts Not Rendering
- **Check**: Chart.js CDN is accessible
- **Check**: Data arrays are properly JSON-encoded
- **Check**: Canvas elements exist in DOM

### Modal Not Opening
- **Check**: Character has detailed markdown file
- **Check**: JavaScript `showChar()` function is defined
- **Check**: Modal CSS is loaded

### Profile Links Not Working
- **Check**: Server names are correct
- **Check**: Character names match exactly (case-sensitive for some sites)

## Configuration

### Raid Buffs
Edit `RAID_BUFFS` dictionary to add/remove buffs:
```python
RAID_BUFFS = {
    'buff_key': {
        'name': 'Display Name',
        'classes': ['Class1', 'Class2'],
        'icon': 'https://...'
    }
}
```

### Colors
- Class colors: Edit `class_colors` dictionary
- Performance colors: Edit `wcl_color()` and `get_rio_color()` functions

### Display Limits
- Top improvers: Line 10 (currently 10)
- M+ runs per character: Line 5 (currently 5)

## Maintenance Guide

### Adding New Features
1. **New Tab**: Add to tab navigation, create tab content div, add JavaScript handler
2. **New Data Source**: Create parser function, integrate into main flow
3. **New Chart**: Add canvas element, initialize Chart.js instance

### Updating Styles
- All CSS in `<style>` block in HTML header
- Use existing class naming conventions
- Test responsive behavior (mobile, tablet, desktop)

### Performance Optimization
- **Large Rosters**: Consider pagination for tables
- **Many Runs**: Implement lazy loading or virtualization
- **File Size**: Minify JavaScript, compress images

## Dependencies

### Required Files
- `logs/Player_data.csv`: Main character data
- `detailed/{name}.md`: Per-character details
- `logs/mplus_enhanced.json`: M+ run data (optional)
- `history_tracker.py`: Guild history data (optional)

### External Libraries
- Chart.js (CDN): For chart rendering
- No other external dependencies

### Python Libraries
- csv, os, json, datetime: Standard library only

## Error Handling

### Missing Data
- CSV not found: Exit with error message
- Markdown missing: Character appears without detail link
- M+ data missing: Display "No M+ Data Available"
- History missing: Empty charts, no top improvers

### Malformed Data
- Invalid CSV row: Skip and log warning
- Unparseable markdown: Use default values
- JSON decode error: Empty trinket list

## Best Practices

1. **Always backup** dashboard.html before regenerating
2. **Test with small dataset** before full roster
3. **Validate CSV format** (correct columns, no special characters)
4. **Check markdown consistency** (use standard format)
5. **Monitor file size** (keep HTML under 5MB for performance)

## Quick Reference

### Generate Dashboard
```bash
python dashboard_generator.py
```

### Input Files
- `logs/Player_data.csv`
- `detailed/*.md`
- `logs/mplus_enhanced.json`

### Output File
- `dashboard.html`

### Key Functions
- `generate_html_dashboard()`: Main entry point
- `parse_wcl_from_markdown()`: WCL data extraction
- `parse_trinkets_from_markdown()`: Trinket data extraction

### Common Issues
1. Syntax errors → Check string escaping in f-strings
2. Broken layout → Verify HTML structure (opening/closing tags)
3. No data → Check file paths and CSV format
4. JavaScript errors → Check browser console
