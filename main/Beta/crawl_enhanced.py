"""
Enhanced crawler integrating the new WCL features
Save as: crawl_enhanced.py
"""
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv

# Import your existing modules
from wcl_enhanced import (
    WarcraftLogsAPI, 
    analyze_performance_consistency,
    calculate_raid_readiness,
    format_recent_activity
)

load_dotenv()

# Use existing imports from your crawl.py
# (Keep all your existing Blizzard API functions)
from crawl import (
    get_character_spec,
    get_character_equipment,
    get_ilvl_from_blizzard,
    get_mplus_score,
    format_amount,
    format_int,
    token_manager
)

# Configuration
WCL_ACCESS_TOKEN = os.getenv("WCL_ACCESS_TOKEN")
REGION = os.getenv("REGION", "kr")

# Initialize enhanced WCL API
wcl_api = WarcraftLogsAPI(WCL_ACCESS_TOKEN)


def crawl_character_enhanced(row, attempt=1):
    """Enhanced character crawl with comprehensive WCL data"""
    server = row["Server"].strip()
    character = row["ID"].strip()
    role = row["Role"].strip()
    character_class = row["Class"].strip()
    
    print(f"[{attempt}] 🔍 Fetching {character}@{server}...")
    
    try:
        # Get basic data (from your existing crawler)
        equipment_data = get_character_equipment(server, character)
        ilvl = get_ilvl_from_blizzard(server, character)
        mplus_score = get_mplus_score(server, character)
        
        # Get spec with icon
        blizzard_spec, blizzard_spec_icon = get_character_spec(server, character)
        
        # Get ENHANCED WCL data
        print(f"  📊 Fetching comprehensive WCL data...")
        wcl_data = wcl_api.get_comprehensive_character_data(
            name=character,
            server=server,
            region=REGION,
            role=role
        )
        
        # Retry logic for failures
        if (not wcl_data or ilvl == 0) and attempt < 3:
            print(f"  ⚠️ Retrying {character}...")
            time.sleep(2)
            return crawl_character_enhanced(row, attempt + 1)
        
        # Process WCL data
        mythic_data = wcl_data.get('mythic', {})
        heroic_data = wcl_data.get('heroic', {})
        recent_activity = wcl_data.get('recent_activity', [])
        
        # Get best performance (prefer mythic, fallback to heroic)
        best_perf_avg = mythic_data.get('best_performance', "N/A")
        if best_perf_avg == "N/A" or best_perf_avg is None:
            best_perf_avg = heroic_data.get('best_performance', "N/A")
        
        # Calculate additional metrics
        mythic_boss_rankings = mythic_data.get('boss_rankings', [])
        consistency_analysis = analyze_performance_consistency(mythic_boss_rankings)
        
        # Calculate raid readiness
        try:
            mplus_val = float(str(mplus_score).replace(',', '')) if mplus_score != "N/A" else 0
            wcl_val = float(str(best_perf_avg).replace(',', '')) if best_perf_avg != "N/A" else 0
            readiness = calculate_raid_readiness(ilvl, mplus_val, wcl_val)
        except:
            readiness = {'score': 0, 'rating': 'Unknown'}
        
        # Get spec from WCL or use Blizzard spec
        all_stars = mythic_data.get('all_stars', [])
        if not all_stars:
            all_stars = heroic_data.get('all_stars', [])
        wcl_spec = all_stars[0].get('spec', blizzard_spec) if all_stars else blizzard_spec
        
        # Save comprehensive report
        os.makedirs("detailed", exist_ok=True)
        report_content = format_comprehensive_report_enhanced(
            character=character,
            character_class=character_class,
            role=role,
            server=server,
            spec=wcl_spec,
            spec_icon=blizzard_spec_icon,
            equipment_data=equipment_data,
            ilvl=ilvl,
            mplus_score=mplus_score,
            wcl_data=wcl_data,
            consistency_analysis=consistency_analysis,
            readiness=readiness
        )
        
        with open(f"detailed/{character}.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"  ✅ {character} complete! (Consistency: {consistency_analysis['consistency_rating']})")
        
        return {
            'csv_row': [
                character,
                character_class,
                wcl_spec,
                ilvl,
                format_amount(mplus_score),
                format_amount(best_perf_avg) if best_perf_avg != "N/A" else "N/A"
            ],
            'enhanced_data': {
                'name': character,
                'server': server,
                'class': character_class,
                'spec': wcl_spec,
                'role': role,
                'ilvl': ilvl,
                'mplus_score': mplus_score,
                'wcl_mythic': mythic_data,
                'wcl_heroic': heroic_data,
                'recent_activity': recent_activity,
                'consistency': consistency_analysis,
                'readiness': readiness
            }
        }
        
    except Exception as e:
        print(f"  ❌ Error for {character}: {e}")
        return {
            'csv_row': [character, character_class, "N/A", 0, "N/A", "N/A"],
            'enhanced_data': None
        }


def format_comprehensive_report_enhanced(character, character_class, role, server, spec, 
                                        spec_icon, equipment_data, ilvl, mplus_score, 
                                        wcl_data, consistency_analysis, readiness):
    """Format enhanced comprehensive report with all new metrics"""
    lines = []
    
    # Header
    lines.append(f"# {character}")
    lines.append(f"**{spec} {character_class}** | **{role}** | **{server}**")
    lines.append(f"**SPEC_ICON:{spec_icon}**")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    lines.append("---\n")
    
    # Get difficulty data
    mythic_data = wcl_data.get('mythic', {})
    heroic_data = wcl_data.get('heroic', {})
    recent_activity = wcl_data.get('recent_activity', [])
    
    # ═══════════════════════════════════════
    # OVERVIEW SECTION (Enhanced)
    # ═══════════════════════════════════════
    lines.append("## 📊 Overview\n")
    lines.append(f"- **Average Item Level:** {ilvl}")
    lines.append(f"- **Mythic+ Score:** {format_amount(mplus_score)}")
    
    mythic_perf = mythic_data.get('best_performance')
    heroic_perf = heroic_data.get('best_performance')
    mythic_median = mythic_data.get('median_performance')
    heroic_median = heroic_data.get('median_performance')
    
    lines.append(f"- **WCL Mythic Best:** {format_amount(mythic_perf)}")
    lines.append(f"- **WCL Mythic Median:** {format_amount(mythic_median)}")
    lines.append(f"- **WCL Heroic Best:** {format_amount(heroic_perf)}")
    lines.append(f"- **WCL Heroic Median:** {format_amount(heroic_median)}\n")
    
    # NEW: Raid Readiness Score
    lines.append("### 🎯 Raid Readiness\n")
    lines.append(f"- **Overall Score:** {readiness['score']:.1f}/100")
    lines.append(f"- **Rating:** {readiness['rating']}")
    lines.append(f"- **Breakdown:**")
    lines.append(f"  - Item Level: {readiness['components']['ilvl']:.1f}/100")
    lines.append(f"  - M+ Experience: {readiness['components']['mplus']:.1f}/100")
    lines.append(f"  - Performance: {readiness['components']['performance']:.1f}/100\n")
    
    # NEW: Consistency Analysis
    if consistency_analysis['total_bosses'] > 0:
        lines.append("### 📈 Performance Consistency\n")
        lines.append(f"- **Consistency Rating:** {consistency_analysis['consistency_rating']}")
        lines.append(f"- **Average Consistency:** {consistency_analysis['average_consistency']:.1f}%")
        lines.append(f"- **Best Boss:** {consistency_analysis.get('best_boss', 'N/A')}")
        lines.append(f"- **Needs Work On:** {consistency_analysis.get('worst_boss', 'N/A')}\n")
    
    # ═══════════════════════════════════════
    # EQUIPMENT SECTION
    # ═══════════════════════════════════════
    lines.append("---\n")
    lines.append("## ⚔️ Equipment\n")
    
    if equipment_data:
        lines.append("| Slot | Item Name | Item Level | Upgrade | Icon |")
        lines.append("|------|-----------|------------|---------|------|")
        
        for item in equipment_data:
            slot = item.get('slot', 'Unknown')
            name = item.get('name', 'Unknown')
            item_ilvl = item.get('ilvl', 0)
            upgrade = item.get('upgrade', 'Unknown')
            icon_url = item.get('icon', '')
            lines.append(f"| {slot} | {name} | {item_ilvl} | {upgrade} | ICON:{icon_url} |")
    else:
        lines.append("*Equipment data not available*")
    
    lines.append("")
    
    # ═══════════════════════════════════════
    # RECENT ACTIVITY SECTION (NEW)
    # ═══════════════════════════════════════
    if recent_activity:
        lines.append("---\n")
        lines.append("## 📅 Recent Raid Activity (Last 2 Weeks)\n")
        lines.append("| Date | Duration | Zone | Kills | Wipes | Bosses |")
        lines.append("|------|----------|------|-------|-------|--------|")
        
        for report in recent_activity[:5]:
            lines.append(
                f"| {report['date']} | "
                f"{report['duration_minutes']:.0f}m | "
                f"{report['zone']} | "
                f"{report['kills']} | "
                f"{report['wipes']} | "
                f"{report['bosses_attempted']} |"
            )
        lines.append("")
    
    # ═══════════════════════════════════════
    # MYTHIC RAIDING SECTION (Enhanced)
    # ═══════════════════════════════════════
    lines.append("---\n")
    lines.append("## 🏆 WarcraftLogs Performance - Mythic\n")
    
    if not mythic_data or mythic_data == {}:
        lines.append("*No mythic raid logs found*\n")
    else:
        if mythic_perf:
            lines.append(f"### Best: **{format_amount(mythic_perf)}** | Median: **{format_amount(mythic_median)}**\n")
        
        lines.append("### 📋 Boss Rankings (Enhanced)\n")
        boss_rankings = mythic_data.get('boss_rankings', [])
        
        if boss_rankings:
            lines.append("| Boss | Best % | Median % | Consistency | DPS/HPS | Kills | Speed |")
            lines.append("|------|--------|----------|-------------|---------|-------|-------|")
            
            for boss in boss_rankings:
                consistency_emoji = "🟢" if boss['consistency_score'] >= 90 else "🟡" if boss['consistency_score'] >= 75 else "🔴"
                lines.append(
                    f"| {boss['boss']} | "
                    f"{format_amount(boss['rank_percent'])}% | "
                    f"{format_amount(boss['median_percent'])}% | "
                    f"{consistency_emoji} {boss['consistency_score']:.0f}% | "
                    f"{format_int(boss['best_amount'])} | "
                    f"{boss['total_kills']} | "
                    f"{boss['fastest_kill'] // 1000}s |"
                )
        else:
            lines.append("*No boss rankings available*")
        
        lines.append("")
    
    # ═══════════════════════════════════════
    # HEROIC RAIDING SECTION (Enhanced)
    # ═══════════════════════════════════════
    lines.append("---\n")
    lines.append("## 🏆 WarcraftLogs Performance - Heroic\n")
    
    if not heroic_data or heroic_data == {}:
        lines.append("*No heroic raid logs found*\n")
    else:
        if heroic_perf:
            lines.append(f"### Best: **{format_amount(heroic_perf)}** | Median: **{format_amount(heroic_median)}**\n")
        
        lines.append("### 📋 Boss Rankings\n")
        boss_rankings = heroic_data.get('boss_rankings', [])
        
        if boss_rankings:
            lines.append("| Boss | Best % | Median % | DPS/HPS | Kills |")
            lines.append("|------|--------|----------|---------|-------|")
            
            for boss in boss_rankings:
                lines.append(
                    f"| {boss['boss']} | "
                    f"{format_amount(boss['rank_percent'])}% | "
                    f"{format_amount(boss['median_percent'])}% | "
                    f"{format_int(boss['best_amount'])} | "
                    f"{boss['total_kills']} |"
                )
        else:
            lines.append("*No boss rankings available*")
        
        lines.append("")
    
    # ═══════════════════════════════════════
    # ALL STARS SECTION
    # ═══════════════════════════════════════
    all_stars = mythic_data.get('all_stars', [])
    if all_stars:
        lines.append("---\n")
        lines.append("## ⭐ All Stars Points\n")
        lines.append("| Partition | Spec | Points | Possible | Rank | Rank % |")
        lines.append("|-----------|------|--------|----------|------|--------|")
        
        for star in all_stars:
            lines.append(
                f"| {star['partition']} | "
                f"{star['spec']} | "
                f"{format_amount(star['points'])} | "
                f"{format_amount(star['possible'])} | "
                f"{star.get('rank', 'N/A')} | "
                f"{format_amount(star['rank_percent'])}% |"
            )
        
        lines.append("")
    
    lines.append("---")
    
    return "\n".join(lines)


def main_enhanced():
    """Enhanced main execution with comprehensive WCL data"""
    start_time = time.time()
    
    # Setup
    os.makedirs("logs", exist_ok=True)
    os.makedirs("detailed", exist_ok=True)
    
    # Load characters
    if not os.path.exists("characters.csv"):
        print("❌ characters.csv not found")
        return
    
    with open("characters.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        characters = list(reader)
    
    print(f"\n🎮 Enhanced Crawler - Fetching {len(characters)} characters")
    print("="*60 + "\n")
    
    results = []
    enhanced_data_all = []
    
    # Process characters
    with ThreadPoolExecutor(max_workers=3) as executor:  # Reduced for API rate limits
        futures = [executor.submit(crawl_character_enhanced, char) for char in characters]
        
        for future in futures:
            result = future.result()
            if result:
                results.append(result['csv_row'])
                if result['enhanced_data']:
                    enhanced_data_all.append(result['enhanced_data'])
    
    # Save CSV
    with open("logs/Player_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Class", "Spec", "ilvl", "M+", "WCL"])
        writer.writerows(results)
    
    # Save enhanced JSON
    import json
    with open("logs/characters_enhanced.json", "w", encoding="utf-8") as f:
        json.dump(enhanced_data_all, f, indent=2, ensure_ascii=False)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Enhanced crawling complete in {elapsed:.1f}s")
    print(f"📁 Results: logs/Player_data.csv")
    print(f"📊 Enhanced data: logs/characters_enhanced.json")
    print(f"📝 Detailed reports: detailed/*.md")
    

if __name__ == "__main__":
    main_enhanced()
