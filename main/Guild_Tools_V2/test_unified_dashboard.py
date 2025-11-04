#!/usr/bin/env python3
"""
Test script for unified dashboard with tabs
"""

print("🎮 Testing Unified Dashboard with Tabs\n")
print("="*60)

# Step 1: Check if we have the required data
import os

print("\n📋 Checking required files...")
files_to_check = [
    ("logs/Player_data.csv", "Character data"),
    ("logs/history.json", "Historical data (optional)"),
    ("logs/mplus_enhanced.json", "Enhanced M+ data (optional)")
]

for filepath, description in files_to_check:
    if os.path.exists(filepath):
        print(f"  ✅ {description}: {filepath}")
    else:
        print(f"  ⚠️ {description}: {filepath} (missing - will use placeholder)")

# Step 2: Generate enhanced M+ data if needed
print("\n🏔️ Generating Enhanced M+ Data...")
print("="*60)

try:
    import mplus_enhanced
    mplus_data = mplus_enhanced.save_enhanced_mplus_data()
    if mplus_data:
        print("✅ Enhanced M+ data generated successfully!")
    else:
        print("⚠️ Could not generate M+ data (characters might not have runs)")
except Exception as e:
    print(f"⚠️ M+ data generation skipped: {e}")

# Step 3: Generate unified dashboard
print("\n📊 Generating Unified Dashboard...")
print("="*60)

try:
    # Import your dashboard generator (adjust name if needed)
    try:
        import generate_dashboard as dash_gen
    except:
        try:
            import dashboard_generator as dash_gen
        except:
            # Try to import directly
            exec(open('generate_dashboard.py').read())
            class dash_gen:
                @staticmethod
                def generate_html_dashboard(csv_file):
                    generate_html_dashboard(csv_file)
    
    dash_gen.generate_html_dashboard("logs/Player_data.csv")
    print("✅ Dashboard generated successfully!")
    
except Exception as e:
    print(f"❌ Dashboard generation failed: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Summary
print("\n" + "="*60)
print("📊 DASHBOARD FEATURES")
print("="*60)
print("  ✅ Tab 1: Overview - Trends & Top Improvers")
print("  ✅ Tab 2: Charts - ilvl, M+, WCL distributions")
print("  ✅ Tab 3: M+ Details - Detailed runs with party info")
print("  ✅ Tab 4: Roster - Full character list")
print("\n📂 Open dashboard.html in your browser to view!")
print("="*60)
