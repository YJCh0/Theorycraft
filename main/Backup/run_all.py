#!/usr/bin/env python3
"""
Master runner script for WoW Guild Dashboard
Runs crawler, updates history, posts to Discord, and generates dashboard
"""

import os
import sys
import importlib
from datetime import datetime

def find_and_import(module_candidates):
    """Try to import module from a list of possible names"""
    for name in module_candidates:
        try:
            return importlib.import_module(name)
        except ImportError:
            continue
    return None

def run_crawler():
    """Run the main crawler to fetch character data"""
    print("\n" + "="*60)
    print("🎮 STEP 1: Running Character Crawler")
    print("="*60)
    
    try:
        # Try to find your crawler module
        crawler = find_and_import(['crawl', 'wow_crawler', 'crawler', 'main_crawler'])
        
        if crawler and hasattr(crawler, 'main'):
            crawler.main()
            return True
        else:
            print("⚠️ Crawler module not found or has no main() function")
            print("💡 Please run your crawler manually first")
            return False
    except Exception as e:
        print(f"❌ Crawler failed: {e}")
        return False

def update_history():
    """Add current snapshot to historical data"""
    print("\n" + "="*60)
    print("📊 STEP 2: Updating Historical Data")
    print("="*60)
    
    try:
        import history_tracker
        return history_tracker.add_current_snapshot()
    except Exception as e:
        print(f"❌ History update failed: {e}")
        return False

def fetch_mplus_data():
    """Fetch detailed M+ dungeon data"""
    print("\n" + "="*60)
    print("🏔️ STEP 3: Fetching M+ Dungeon Breakdown")
    print("="*60)
    
    try:
        import mplus_enhanced
        mplus_data = mplus_enhanced.save_enhanced_mplus_data()
        return mplus_data is not None
    except Exception as e:
        print(f"❌ M+ data fetch failed: {e}")
        return False

def post_to_discord():
    """Post updates to Discord"""
    print("\n" + "="*60)
    print("📢 STEP 4: Posting to Discord")
    print("="*60)
    
    try:
        import discord_integration
        from history_tracker import get_top_improvers
        import csv
        
        # Check if webhook is configured
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        if not webhook_url:
            print("⚠️ Discord webhook not configured (skipping)")
            print("💡 Add DISCORD_WEBHOOK_URL to your .env file to enable Discord posts")
            return True
        
        # Get current stats
        if os.path.exists("logs/Player_data.csv"):
            with open("logs/Player_data.csv", 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                chars = list(reader)
                
                if not chars:
                    print("⚠️ No character data found")
                    return True
                
                total_chars = len(chars)
                
                # Calculate averages safely
                ilvls = []
                mplus = []
                wcl = []
                
                for c in chars:
                    try:
                        if c['ilvl'] != 'N/A':
                            ilvls.append(float(c['ilvl']))
                    except:
                        pass
                    
                    try:
                        if c['M+'] != 'N/A':
                            mplus.append(float(str(c['M+']).replace(',', '')))
                    except:
                        pass
                    
                    try:
                        if c['WCL'] != 'N/A':
                            wcl.append(float(str(c['WCL']).replace(',', '')))
                    except:
                        pass
                
                avg_ilvl = sum(ilvls) / len(ilvls) if ilvls else 0
                avg_mplus = sum(mplus) / len(mplus) if mplus else 0
                avg_wcl = sum(wcl) / len(wcl) if wcl else 0
                
                # Post guild summary with dashboard link
                dashboard_url = os.getenv("DASHBOARD_URL")  # Optional: public URL to your dashboard
                discord_integration.post_guild_summary(total_chars, avg_ilvl, avg_mplus, avg_wcl, dashboard_url)
                
                # Post top improvers
                improvers = get_top_improvers(7)
                if improvers:
                    discord_integration.post_top_improvers(improvers)
                else:
                    print("ℹ️ No improvers to post (need multiple snapshots)")
                
                # Check for milestones
                discord_integration.check_and_post_milestones()
        
        return True
    except Exception as e:
        print(f"⚠️ Discord posting failed (optional): {e}")
        return True  # Don't fail the whole process

def generate_dashboard():
    """Generate the HTML dashboard"""
    print("\n" + "="*60)
    print("📊 STEP 5: Generating Dashboard")
    print("="*60)
    
    try:
        # Try to find dashboard generator
        dashboard_gen = find_and_import(['generate_html_dashboard', 'dashboard_generator', 'dashboard', 'generate_dashboard'])
        
        if dashboard_gen and hasattr(dashboard_gen, 'generate_html_dashboard'):
            dashboard_gen.generate_html_dashboard("logs/Player_data.csv")
            return True
        else:
            print("⚠️ Dashboard generator not found")
            print("💡 Please run your dashboard generator manually")
            return False
    except Exception as e:
        print(f"❌ Dashboard generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all steps in sequence"""
    print("\n" + "="*60)
    print("🚀 WoW Guild Dashboard - Full Update")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {
        'crawler': False,
        'history': False,
        'mplus': False,
        'discord': False,
        'dashboard': False
    }
    
    # Step 1: Run crawler
    results['crawler'] = run_crawler()
    if not results['crawler']:
        print("\n⚠️ Crawler step failed or skipped")
        print("💡 Make sure you have Player_data.csv in logs/ directory")
    
    # Check if we have data to continue
    if not os.path.exists("logs/Player_data.csv"):
        print("\n❌ No Player_data.csv found. Cannot continue.")
        print("💡 Run your crawler first to generate character data")
        sys.exit(1)
    
    # Step 2: Update history
    results['history'] = update_history()
    if not results['history']:
        print("\n⚠️ History update failed, but continuing...")
    
    # Step 3: Fetch M+ data
    results['mplus'] = fetch_mplus_data()
    if not results['mplus']:
        print("\n⚠️ M+ data fetch failed, but continuing...")
    
    # Step 4: Post to Discord
    results['discord'] = post_to_discord()
    
    # Step 5: Generate dashboard
    results['dashboard'] = generate_dashboard()
    if not results['dashboard']:
        print("\n⚠️ Dashboard generation failed")
    
    # Summary
    print("\n" + "="*60)
    print("📋 EXECUTION SUMMARY")
    print("="*60)
    print(f"  {'✅' if results['crawler'] else '⚠️'} Character data crawled")
    print(f"  {'✅' if results['history'] else '⚠️'} Historical data updated")
    print(f"  {'✅' if results['mplus'] else '⚠️'} M+ dungeon breakdown fetched")
    print(f"  {'✅' if results['discord'] else '⚠️'} Discord notifications sent")
    print(f"  {'✅' if results['dashboard'] else '⚠️'} Dashboard generated")
    
    if results['dashboard']:
        print("\n✅ SUCCESS! Dashboard is ready")
        print("📊 Open dashboard.html in your browser to view!")
    else:
        print("\n⚠️ Some steps failed, but partial data may be available")
    
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
