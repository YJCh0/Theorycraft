#!/usr/bin/env python3
"""
Master Runner Script v2.0 - STANDALONE Edition
No dependencies on original code
Save as: run_all.py
"""
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def verify_requirements():
    """Verify all required files and configurations"""
    print_section("🔍 Pre-flight Checks")
    
    checks = {
        'characters.csv': os.path.exists('characters.csv'),
        '.env file': os.path.exists('.env'),
        'wcl_enhanced.py': os.path.exists('wcl_enhanced.py'),
        'crawl_standalone.py': os.path.exists('crawl_standalone.py'),
        'guild_analytics.py': os.path.exists('guild_analytics.py'),
        'WCL_ACCESS_TOKEN': bool(os.getenv('WCL_ACCESS_TOKEN')),
        'BLIZZARD_CLIENT_ID': bool(os.getenv('BLIZZARD_CLIENT_ID')),
        'BLIZZARD_CLIENT_SECRET': bool(os.getenv('BLIZZARD_CLIENT_SECRET'))
    }
    
    all_good = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
        if not passed:
            all_good = False
    
    if not all_good:
        print("\n⚠️ Some requirements are missing!")
        print("\n💡 Required files:")
        print("   1. characters.csv - Your guild roster")
        print("   2. .env - API credentials")
        print("   3. wcl_enhanced.py")
        print("   4. crawl_standalone.py")
        print("   5. guild_analytics.py")
        print("   6. generate_dashboard_enhanced.py")
        return False
    
    print("\n✅ All checks passed!")
    return True

def run_crawler():
    """Run standalone crawler"""
    print_section("🎮 STEP 1: Enhanced Crawler")
    
    try:
        import crawl_standalone
        crawl_standalone.main()
        return True
    except Exception as e:
        print(f"❌ Crawler failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_history():
    """Update historical data"""
    print_section("📊 STEP 2: Historical Data")
    
    # Check if history tracker exists
    if not os.path.exists('history_tracker.py'):
        print("⚠️ history_tracker.py not found - creating minimal version...")
        
        # Create basic history tracker
        create_basic_history_tracker()
        
    try:
        import history_tracker
        success = history_tracker.add_current_snapshot()
        
        if success:
            trends = history_tracker.get_guild_average_history()
            if trends['dates']:
                print(f"✅ Snapshot added for {trends['dates'][-1]}")
        
        return success
    except Exception as e:
        print(f"⚠️ History update failed: {e}")
        return False

def fetch_mplus_data():
    """Fetch M+ data"""
    print_section("🏔️ STEP 3: M+ Data")
    
    # Check if mplus_enhanced exists
    if not os.path.exists('mplus_enhanced.py'):
        print("⚠️ mplus_enhanced.py not found - skipping M+ detailed data")
        return True  # Don't fail, just skip
    
    try:
        import mplus_enhanced
        mplus_data = mplus_enhanced.save_recent_mplus_data("logs/Player_data.csv")
        return mplus_data is not None
    except Exception as e:
        print(f"⚠️ M+ fetch failed: {e}")
        return True  # Don't fail pipeline

def run_guild_analytics():
    """Run guild analytics"""
    print_section("🎯 STEP 4: Guild Analytics")
    
    try:
        from guild_analytics import GuildAnalytics, print_analytics_summary
        
        analytics = GuildAnalytics()
        
        if not analytics.characters:
            print("⚠️ No enhanced character data found")
            return False
        
        analytics.export_analytics_report()
        print_analytics_summary(analytics)
        
        return True
    except Exception as e:
        print(f"⚠️ Analytics failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def post_to_discord():
    """Post to Discord"""
    print_section("📢 STEP 5: Discord")
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        print("ℹ️ Discord webhook not configured (skipping)")
        return True
    
    # Check if discord integration exists
    if not os.path.exists('discord_integration.py'):
        print("⚠️ discord_integration.py not found - skipping Discord")
        return True
    
    try:
        import discord_integration
        import csv
        
        if not os.path.exists("logs/Player_data.csv"):
            return False
        
        with open("logs/Player_data.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            chars = list(reader)
        
        if not chars:
            return True
        
        # Calculate averages
        total = len(chars)
        ilvls = [float(c['ilvl']) for c in chars if c['ilvl'] != 'N/A']
        mplus = [float(str(c['M+']).replace(',', '')) for c in chars if c['M+'] != 'N/A']
        wcl = [float(str(c['WCL']).replace(',', '')) for c in chars if c['WCL'] != 'N/A']
        
        avg_ilvl = sum(ilvls)/len(ilvls) if ilvls else 0
        avg_mplus = sum(mplus)/len(mplus) if mplus else 0
        avg_wcl = sum(wcl)/len(wcl) if wcl else 0
        
        # Post
        dashboard_url = os.getenv("DASHBOARD_URL")
        discord_integration.post_guild_summary(total, avg_ilvl, avg_mplus, avg_wcl, dashboard_url)
        
        return True
    except Exception as e:
        print(f"⚠️ Discord posting failed: {e}")
        return True

def generate_dashboard():
    """Generate dashboard"""
    print_section("📊 STEP 6: Dashboard")
    
    try:
        import generate_dashboard_enhanced
        generate_dashboard_enhanced.generate_enhanced_dashboard()
        return True
    except Exception as e:
        print(f"❌ Dashboard generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_basic_history_tracker():
    """Create basic history tracker if it doesn't exist"""
    code = '''import json
import os
import csv
from datetime import datetime

HISTORY_FILE = "logs/history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_history(history):
    os.makedirs("logs", exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def add_current_snapshot():
    if not os.path.exists("logs/Player_data.csv"):
        return False
    
    current_data = {}
    with open("logs/Player_data.csv", 'r', encoding='utf-8') as f:
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
            except:
                continue
    
    history = load_history()
    timestamp = datetime.now().strftime('%Y-%m-%d')
    history[timestamp] = current_data
    
    # Keep only last 30 days
    dates = sorted(history.keys())
    if len(dates) > 30:
        for old_date in dates[:-30]:
            del history[old_date]
    
    save_history(history)
    print(f"✅ Snapshot added for {timestamp}")
    return True

def get_guild_average_history():
    history = load_history()
    guild_history = {'dates': [], 'avg_ilvl': [], 'avg_mplus': [], 'avg_wcl': []}
    
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
    return []
'''
    
    with open('history_tracker.py', 'w') as f:
        f.write(code)
    
    print("✅ Created basic history_tracker.py")

def main():
    """Run complete pipeline"""
    start_time = time.time()
    
    print("\n" + "="*60)
    print("  🚀 WoW Guild Dashboard - Standalone v2.0")
    print(f"  ⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Verify
    if not verify_requirements():
        print("\n❌ Pre-flight checks failed. Exiting.")
        sys.exit(1)
    
    results = {
        'crawler': False,
        'history': False,
        'mplus': False,
        'analytics': False,
        'discord': False,
        'dashboard': False
    }
    
    # Run pipeline
    results['crawler'] = run_crawler()
    if not results['crawler']:
        print("\n❌ Crawler failed. Cannot continue.")
        sys.exit(1)
    
    if not os.path.exists("logs/Player_data.csv"):
        print("\n❌ No player data. Exiting.")
        sys.exit(1)
    
    results['history'] = update_history()
    results['mplus'] = fetch_mplus_data()
    results['analytics'] = run_guild_analytics()
    results['discord'] = post_to_discord()
    results['dashboard'] = generate_dashboard()
    
    # Summary
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print("  📋 SUMMARY")
    print("="*60)
    print(f"  {'✅' if results['crawler'] else '❌'} Character data")
    print(f"  {'✅' if results['history'] else '⚠️'} Historical data")
    print(f"  {'✅' if results['mplus'] else '⚠️'} M+ data")
    print(f"  {'✅' if results['analytics'] else '⚠️'} Analytics")
    print(f"  {'✅' if results['discord'] else '⚠️'} Discord")
    print(f"  {'✅' if results['dashboard'] else '❌'} Dashboard")
    print("="*60)
    
    if results['dashboard']:
        print("\n🎉 SUCCESS! Dashboard ready!")
        print("📊 Open dashboard.html")
        print("\n📁 Generated files:")
        print("   - dashboard.html")
        print("   - logs/Player_data.csv")
        print("   - logs/characters_enhanced.json")
        print("   - logs/guild_analytics.json")
        print("   - detailed/*.md")
    else:
        print("\n⚠️ Dashboard failed, but data available")
    
    print(f"\n⏰ Completed in {elapsed:.1f}s")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
