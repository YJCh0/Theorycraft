import csv
import os
import json
from datetime import datetime
from collections import defaultdict

HISTORY_FILE = "logs/history.json"
CURRENT_DATA_FILE = "logs/Player_data.csv"

def load_history():
    """Load historical data from JSON file"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_history(history):
    """Save historical data to JSON file"""
    os.makedirs("logs", exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def add_current_snapshot():
    """Add current data as a new snapshot in history"""
    if not os.path.exists(CURRENT_DATA_FILE):
        print("❌ Current data file not found")
        return False
    
    # Load current data
    current_data = {}
    with open(CURRENT_DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                current_data[row['ID']] = {
                    'ilvl': float(row['ilvl']) if row['ilvl'] != 'N/A' else 0,
                    'mplus': float(str(row['M+']).replace(',', '')) if row['M+'] != 'N/A' else 0,
                    'wcl': float(str(row['WCL']).replace(',', '')) if row['WCL'] != 'N/A' else 0,
                    'class': row['Class'],
                    'spec': row['Spec']
                }
            except (ValueError, KeyError) as e:
                print(f"⚠️ Error parsing {row.get('ID', 'unknown')}: {e}")
                continue
    
    if not current_data:
        print("❌ No valid character data found")
        return False
    
    # Load history
    history = load_history()
    
    # Get current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d')
    
    # Check if we already have data for today (don't duplicate)
    if timestamp in history:
        print(f"⚠️ Data for {timestamp} already exists. Updating...")
    
    # Add current snapshot
    history[timestamp] = current_data
    
    # Keep only last 30 days
    dates = sorted(history.keys())
    if len(dates) > 30:
        for old_date in dates[:-30]:
            del history[old_date]
    
    # Save updated history
    save_history(history)
    print(f"✅ Snapshot added for {timestamp}")
    print(f"📊 Total snapshots: {len(history)}")
    return True

def get_character_history(character_name):
    """Get historical data for a specific character"""
    history = load_history()
    
    char_history = {
        'dates': [],
        'ilvl': [],
        'mplus': [],
        'wcl': []
    }
    
    for date in sorted(history.keys()):
        if character_name in history[date]:
            char_data = history[date][character_name]
            char_history['dates'].append(date)
            char_history['ilvl'].append(char_data['ilvl'])
            char_history['mplus'].append(char_data['mplus'])
            char_history['wcl'].append(char_data['wcl'])
    
    return char_history

def get_guild_average_history():
    """Get guild average trends over time"""
    history = load_history()
    
    guild_history = {
        'dates': [],
        'avg_ilvl': [],
        'avg_mplus': [],
        'avg_wcl': []
    }
    
    for date in sorted(history.keys()):
        ilvls = [data['ilvl'] for data in history[date].values() if data['ilvl'] > 0]
        mplus = [data['mplus'] for data in history[date].values() if data['mplus'] > 0]
        wcl = [data['wcl'] for data in history[date].values() if data['wcl'] > 0]
        
        guild_history['dates'].append(date)
        guild_history['avg_ilvl'].append(sum(ilvls) / len(ilvls) if ilvls else 0)
        guild_history['avg_mplus'].append(sum(mplus) / len(mplus) if mplus else 0)
        guild_history['avg_wcl'].append(sum(wcl) / len(wcl) if wcl else 0)
    
    return guild_history

def get_top_improvers(days=7):
    """Get characters with biggest improvements in last N days"""
    history = load_history()
    dates = sorted(history.keys())
    
    if len(dates) < 2:
        print("⚠️ Need at least 2 snapshots to calculate improvements")
        return []
    
    # Get recent dates (last N days)
    recent_dates = dates[-min(days + 1, len(dates)):]
    oldest_date = recent_dates[0]
    newest_date = recent_dates[-1]
    
    print(f"📊 Comparing {oldest_date} → {newest_date}")
    
    improvements = []
    
    # Find characters that exist in both snapshots
    for char_name in history[newest_date].keys():
        if char_name in history[oldest_date]:
            old_data = history[oldest_date][char_name]
            new_data = history[newest_date][char_name]
            
            ilvl_gain = new_data['ilvl'] - old_data['ilvl']
            mplus_gain = new_data['mplus'] - old_data['mplus']
            wcl_gain = new_data['wcl'] - old_data['wcl']
            
            # Calculate improvement score (weighted)
            improvement_score = (ilvl_gain * 2) + (mplus_gain * 0.01) + (wcl_gain * 0.5)
            
            improvements.append({
                'name': char_name,
                'class': new_data['class'],
                'spec': new_data['spec'],
                'ilvl_gain': ilvl_gain,
                'mplus_gain': mplus_gain,
                'wcl_gain': wcl_gain,
                'score': improvement_score
            })
    
    # Sort by improvement score
    improvements.sort(key=lambda x: x['score'], reverse=True)
    
    return improvements[:10]  # Top 10

if __name__ == "__main__":
    print("📊 Historical Data Tracker\n")
    
    # Add current snapshot
    success = add_current_snapshot()
    
    if not success:
        print("\n❌ Failed to add snapshot")
        exit(1)
    
    # Show guild trends
    print("\n📈 Guild Average Trends:")
    guild_trends = get_guild_average_history()
    if guild_trends['dates']:
        print(f"   Dates tracked: {len(guild_trends['dates'])}")
        if guild_trends['avg_ilvl']:
            print(f"   Latest ilvl: {guild_trends['avg_ilvl'][-1]:.1f}")
            print(f"   Latest M+: {guild_trends['avg_mplus'][-1]:.1f}")
            print(f"   Latest WCL: {guild_trends['avg_wcl'][-1]:.1f}")
    else:
        print("   No historical data yet")
    
    # Show top improvers
    print("\n🏆 Top Improvers (Last 7 Days):")
    improvers = get_top_improvers(7)
    if improvers:
        for i, player in enumerate(improvers[:5], 1):
            print(f"   {i}. {player['name']} ({player['spec']} {player['class']})")
            print(f"      ilvl: +{player['ilvl_gain']:.1f} | M+: +{player['mplus_gain']:.0f} | WCL: +{player['wcl_gain']:.1f}")
    else:
        print("   No improvement data yet (need multiple snapshots)")
