#!/usr/bin/env python3
"""
Master Runner Script v2.0 - Enhanced Edition
Runs all enhanced modules in sequence
Save as: run_enhanced.py
"""
import os
import sys
import time
from datetime import datetime

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def run_enhanced_crawler():
    """Run the enhanced crawler with comprehensive WCL data"""
    print_section("🎮 STEP 1: Enhanced Character Crawler")
    
    try:
        import crawl_enhanced
        crawl_enhanced.main_enhanced()
        return True
    except Exception as e:
        print(f"❌ Enhanced crawler failed: {e}")
        print("💡 Trying fallback to standard crawler...")
        try:
            import crawl
            crawl.main()
            return True
        except:
            return False

def update_history():
    """Add current snapshot to historical tracking"""
    print_section("📊 STEP 2: Historical Data Update")
    
    try:
        import history_tracker
        success = history_tracker.add_current_snapshot()
        
        if success:
            # Show quick stats
            trends = history_tracker.get_guild_average_history()
            if trends['dates']:
                print(f"✅ Snapshot added for {trends['dates'][-1]}")
                print(f"   Latest ilvl: {trends['avg_ilvl'][-1]:.1f}")
                print(f"   Latest M+: {trends['avg_mplus'][-1]:.1f}")
                print(f"   Latest WCL: {trends['avg_wcl'][-1]:.1f}")
        
        return success
    except Exception as e:
        print(f"⚠️ History update failed: {e}")
        return False

def fetch_mplus_data():
    """Fetch detailed M+ dungeon breakdown"""
    print_section("🏔️ STEP 3: M+ Dungeon Breakdown")
    
    try:
        import mplus_enhanced
        mplus_data = mplus_enhanced.save_recent_mplus_data("logs/Player_data.csv")
        return mplus_data is not None
    except Exception as e:
        print(f"⚠️ M+ fetch failed: {e}")
        return False

def run_guild_analytics():
    """Run comprehensive guild analytics"""
    print_section("🎯 STEP 4: Guild Analytics")
    
    try:
        from guild_analytics import GuildAnalytics, print_analytics_summary
        
        analytics = GuildAnalytics()
        
        if not analytics.characters:
            print("⚠️ No enhanced character data found")
            return False
        
        # Generate report
        analytics.export_analytics_report()
        
        # Print summary
        print_analytics_summary(analytics)
        
        return True
    except Exception as e:
        print(f"⚠️ Analytics failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def post_to_discord():
    """Post updates to Discord"""
    print_section("📢 STEP 5: Discord Notifications")
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        print("ℹ️ Discord webhook not configured (skipping)")
        print("💡 Add DISCORD_WEBHOOK_URL to .env to enable")
        return True
    
    try:
        import discord_integration
        from history_tracker import get_top_improvers
        import csv
        
        # Load current stats
        if not os.path.exists("logs/Player_data.csv"):
            print("⚠️ No player data found")
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
        
        # Post summary
        dashboard_url = os.getenv("DASHBOARD_URL")
        discord_integration.post_guild_summary(total, avg_ilvl, avg_mplus, avg_wcl, dashboard_url)
        
        # Post top improvers
        improvers = get_top_improvers(7)
        if improvers:
            discord_integration.post_top_improvers(improvers)
        
        # Check milestones
        discord_integration.check_and_post_milestones()
        
        return True
    except Exception as e:
        print(f"⚠️ Discord posting failed: {e}")
        return True  # Don't fail entire pipeline

def generate_enhanced_dashboard():
    """Generate the enhanced HTML dashboard"""
    print_section("📊 STEP 6: Enhanced Dashboard Generation")
    
    try:
        import generate_dashboard_enhanced
        generate_dashboard_enhanced.generate_enhanced_dashboard()
        return True
    except Exception as e:
        print(f"❌ Dashboard generation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Try fallback to original dashboard
        print("\n💡 Attempting fallback to standard dashboard...")
        try:
            import generate_html_dashboard
            generate_html_dashboard.generate_html_dashboard("logs/Player_data.csv")
            return True
        except:
            return False

def verify_requirements():
    """Verify all required files and configurations"""
    print_section("🔍 Pre-flight Checks")
    
    checks = {
        'characters.csv': os.path.exists('characters.csv'),
        '.env file': os.path.exists('.env'),
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
        print("💡 Make sure you have:")
        print("   1. characters.csv with your guild roster")
        print("   2. .env file with API credentials")
        print("   3. All required Python packages installed")
        return False
    
    print("\n✅ All checks passed!")
    return True

def main():
    """Run complete enhanced pipeline"""
    start_time = time.time()
    
    print("\n" + "="*60)
    print("  🚀 WoW Guild Dashboard - Enhanced Edition v2.0")
    print(f"  ⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Verify requirements
    if not verify_requirements():
        print("\n❌ Pre-flight checks failed. Exiting.")
        sys.exit(1)
    
    # Track results
    results = {
        'crawler': False,
        'history': False,
        'mplus': False,
        'analytics': False,
        'discord': False,
        'dashboard': False
    }
    
    # Step 1: Enhanced Crawler
    results['crawler'] = run_enhanced_crawler()
    if not results['crawler']:
        print("\n❌ Crawler failed. Cannot continue.")
        sys.exit(1)
    
    # Check for data
    if not os.path.exists("logs/Player_data.csv"):
        print("\n❌ No player data generated. Exiting.")
        sys.exit(1)
    
    # Step 2: History
    results['history'] = update_history()
    
    # Step 3: M+ Data
    results['mplus'] = fetch_mplus_data()
    
    # Step 4: Guild Analytics (NEW!)
    results['analytics'] = run_guild_analytics()
    
    # Step 5: Discord
    results['discord'] = post_to_discord()
    
    # Step 6: Enhanced Dashboard
    results['dashboard'] = generate_enhanced_dashboard()
    
    # Summary
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print("  📋 EXECUTION SUMMARY")
    print("="*60)
    print(f"  {'✅' if results['crawler'] else '❌'} Enhanced character data crawled")
    print(f"  {'✅' if results['history'] else '⚠️'} Historical data updated")
    print(f"  {'✅' if results['mplus'] else '⚠️'} M+ dungeon breakdown fetched")
    print(f"  {'✅' if results['analytics'] else '⚠️'} Guild analytics generated")
    print(f"  {'✅' if results['discord'] else '⚠️'} Discord notifications sent")
    print(f"  {'✅' if results['dashboard'] else '❌'} Enhanced dashboard generated")
    print("="*60)
    
    if results['dashboard']:
        print("\n🎉 SUCCESS! Enhanced dashboard is ready!")
        print("📊 Open dashboard.html in your browser")
        print("\n📁 Generated files:")
        print("   - dashboard.html (Main dashboard)")
        print("   - logs/Player_data.csv (Character data)")
        print("   - logs/characters_enhanced.json (Enhanced data)")
        print("   - logs/guild_analytics.json (Analytics report)")
        print("   - logs/mplus_enhanced.json (M+ details)")
        print("   - detailed/*.md (Individual character reports)")
    else:
        print("\n⚠️ Dashboard generation failed, but data is available")
    
    print(f"\n⏰ Completed in {elapsed:.1f}s")
    print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    print("💡 New Features:")
    print("   ✨ Enhanced WCL data with consistency tracking")
    print("   ✨ Raid readiness scores")
    print("   ✨ Guild analytics and recommendations")
    print("   ✨ 7-tab dashboard with composition analysis")
    print("   ✨ Performance trends and improvements")
    

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
