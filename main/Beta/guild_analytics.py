"""
Guild-wide analytics and roster composition analysis
Save as: guild_analytics.py
"""
import json
import os
from typing import List, Dict
from collections import defaultdict
from datetime import datetime

class GuildAnalytics:
    """Comprehensive guild analytics and roster analysis"""
    
    # Class utility mapping
    CLASS_UTILITIES = {
        'Warrior': ['battle_shout', 'rallying_cry'],
        'Paladin': ['devotion_aura', 'blessings', 'lay_on_hands'],
        'Hunter': ['hunters_mark', 'bloodlust', 'combat_res'],
        'Rogue': ['numbing_poison', 'tricks', 'shroud'],
        'Priest': ['power_word_fortitude', 'mass_dispel', 'pain_suppression'],
        'Shaman': ['skyfury', 'bloodlust', 'wind_shear'],
        'Mage': ['arcane_intellect', 'bloodlust', 'mass_invis'],
        'Warlock': ['healthstone', 'gateway', 'combat_res'],
        'Monk': ['mystic_touch', 'ring_of_peace'],
        'Druid': ['mark_of_the_wild', 'combat_res', 'roar'],
        'Demon Hunter': ['chaos_brand', 'darkness'],
        'Demonhunter': ['chaos_brand', 'darkness'],
        'Death Knight': ['death_grip', 'anti_magic_zone'],
        'Deathknight': ['death_grip', 'anti_magic_zone'],
        'Evoker': ['blessing_of_the_bronze', 'combat_res']
    }
    
    # Role distribution by spec
    SPEC_ROLES = {
        'Tank': ['Protection', 'Guardian', 'Blood', 'Brewmaster', 'Vengeance'],
        'Healer': ['Holy', 'Discipline', 'Restoration', 'Mistweaver', 'Preservation'],
        'Melee': ['Arms', 'Fury', 'Retribution', 'Enhancement', 'Feral', 'Survival', 
                  'Assassination', 'Outlaw', 'Subtlety', 'Windwalker', 'Havoc', 'Frost (DK)', 'Unholy'],
        'Ranged': ['Fire', 'Frost (Mage)', 'Arcane', 'Shadow', 'Balance', 'Elemental',
                   'Affliction', 'Demonology', 'Destruction', 'Beast Mastery', 'Marksmanship',
                   'Devastation', 'Augmentation']
    }
    
    def __init__(self, enhanced_data_file: str = "logs/characters_enhanced.json"):
        """Initialize with enhanced character data"""
        self.characters = []
        if os.path.exists(enhanced_data_file):
            with open(enhanced_data_file, 'r', encoding='utf-8') as f:
                self.characters = json.load(f)
        else:
            print(f"⚠️ Enhanced data file not found: {enhanced_data_file}")
    
    def analyze_roster_composition(self) -> Dict:
        """Analyze overall roster composition"""
        if not self.characters:
            return {}
        
        composition = {
            'total': len(self.characters),
            'by_class': defaultdict(int),
            'by_role': {'Tank': 0, 'Healer': 0, 'Melee': 0, 'Ranged': 0},
            'by_spec': defaultdict(int),
            'armor_types': {'Plate': 0, 'Mail': 0, 'Leather': 0, 'Cloth': 0}
        }
        
        armor_map = {
            'Warrior': 'Plate', 'Paladin': 'Plate', 'Death Knight': 'Plate', 'Deathknight': 'Plate',
            'Hunter': 'Mail', 'Shaman': 'Mail', 'Evoker': 'Mail',
            'Rogue': 'Leather', 'Monk': 'Leather', 'Druid': 'Leather', 'Demon Hunter': 'Leather', 'Demonhunter': 'Leather',
            'Mage': 'Cloth', 'Warlock': 'Cloth', 'Priest': 'Cloth'
        }
        
        for char in self.characters:
            char_class = char['class']
            char_spec = char['spec']
            
            composition['by_class'][char_class] += 1
            composition['by_spec'][char_spec] += 1
            
            # Determine role
            role = char.get('role', 'DPS')
            if role == 'TANK':
                composition['by_role']['Tank'] += 1
            elif role == 'HEALING':
                composition['by_role']['Healer'] += 1
            else:
                # Check if melee or ranged
                is_melee = any(spec in char_spec for spec in self.SPEC_ROLES['Melee'])
                if is_melee:
                    composition['by_role']['Melee'] += 1
                else:
                    composition['by_role']['Ranged'] += 1
            
            # Armor type
            armor = armor_map.get(char_class, 'Unknown')
            if armor in composition['armor_types']:
                composition['armor_types'][armor] += 1
        
        return composition
    
    def check_utility_coverage(self) -> Dict:
        """Check which raid utilities are covered"""
        coverage = {
            'bloodlust': [],
            'combat_res': [],
            'immunities': [],
            'raid_buffs': [],
            'missing_utilities': []
        }
        
        bloodlust_classes = ['Shaman', 'Hunter', 'Mage', 'Evoker']
        combat_res_classes = ['Druid', 'Warlock', 'Death Knight', 'Deathknight', 'Evoker']
        
        present_classes = set(char['class'] for char in self.characters)
        
        for char in self.characters:
            char_class = char['class']
            
            if char_class in bloodlust_classes:
                if char['name'] not in coverage['bloodlust']:
                    coverage['bloodlust'].append(char['name'])
            
            if char_class in combat_res_classes:
                if char['name'] not in coverage['combat_res']:
                    coverage['combat_res'].append(char['name'])
        
        # Check missing key utilities
        if not any(c in present_classes for c in bloodlust_classes):
            coverage['missing_utilities'].append('Bloodlust')
        
        if not any(c in present_classes for c in combat_res_classes):
            coverage['missing_utilities'].append('Combat Resurrection')
        
        return coverage
    
    def analyze_raid_performance(self) -> Dict:
        """Analyze guild raid performance"""
        analysis = {
            'active_raiders': 0,
            'performance_tiers': {
                'excellent': [],  # 95+
                'good': [],       # 75-94
                'average': [],    # 50-74
                'needs_work': []  # <50
            },
            'consistency_analysis': {
                'excellent': [],
                'good': [],
                'inconsistent': []
            },
            'readiness_by_tier': {
                'mythic_ready': [],
                'heroic_ready': [],
                'needs_improvement': []
            }
        }
        
        for char in self.characters:
            # Check if has raid logs
            mythic_data = char.get('wcl_mythic', {})
            heroic_data = char.get('wcl_heroic', {})
            
            if not mythic_data and not heroic_data:
                continue
            
            analysis['active_raiders'] += 1
            
            # Performance tier
            best_perf = mythic_data.get('best_performance', 0)
            if not best_perf or best_perf == "N/A":
                best_perf = heroic_data.get('best_performance', 0)
            
            try:
                best_perf = float(best_perf) if best_perf != "N/A" else 0
                
                if best_perf >= 95:
                    analysis['performance_tiers']['excellent'].append({
                        'name': char['name'],
                        'score': best_perf
                    })
                elif best_perf >= 75:
                    analysis['performance_tiers']['good'].append({
                        'name': char['name'],
                        'score': best_perf
                    })
                elif best_perf >= 50:
                    analysis['performance_tiers']['average'].append({
                        'name': char['name'],
                        'score': best_perf
                    })
                else:
                    analysis['performance_tiers']['needs_work'].append({
                        'name': char['name'],
                        'score': best_perf
                    })
            except:
                pass
            
            # Consistency
            consistency = char.get('consistency', {})
            rating = consistency.get('consistency_rating', 'Unknown')
            
            if rating in ['Excellent', 'Good']:
                analysis['consistency_analysis']['excellent'].append(char['name'])
            elif rating == 'Average':
                analysis['consistency_analysis']['good'].append(char['name'])
            else:
                analysis['consistency_analysis']['inconsistent'].append(char['name'])
            
            # Readiness
            readiness = char.get('readiness', {})
            readiness_rating = readiness.get('rating', 'Unknown')
            
            if readiness_rating == 'Mythic Ready':
                analysis['readiness_by_tier']['mythic_ready'].append(char['name'])
            elif readiness_rating == 'Heroic Ready':
                analysis['readiness_by_tier']['heroic_ready'].append(char['name'])
            else:
                analysis['readiness_by_tier']['needs_improvement'].append(char['name'])
        
        return analysis
    
    def get_roster_recommendations(self) -> List[str]:
        """Get actionable roster recommendations"""
        recommendations = []
        
        composition = self.analyze_roster_composition()
        utility = self.check_utility_coverage()
        performance = self.analyze_raid_performance()
        
        # Role balance check
        roles = composition['by_role']
        if roles['Tank'] < 2:
            recommendations.append(f"⚠️ Need more tanks (current: {roles['Tank']}, recommended: 2-3)")
        if roles['Healer'] < 4:
            recommendations.append(f"⚠️ Need more healers (current: {roles['Healer']}, recommended: 4-5)")
        
        # Ranged vs Melee balance
        total_dps = roles['Melee'] + roles['Ranged']
        if total_dps > 0:
            ranged_percent = (roles['Ranged'] / total_dps) * 100
            if ranged_percent < 30:
                recommendations.append(f"⚠️ Low ranged DPS ratio ({ranged_percent:.0f}%, recommended: 30-50%)")
        
        # Utility coverage
        if utility['missing_utilities']:
            recommendations.append(f"⚠️ Missing utilities: {', '.join(utility['missing_utilities'])}")
        
        if len(utility['bloodlust']) < 2:
            recommendations.append("⚠️ Insufficient Bloodlust coverage (need 2+ sources)")
        
        if len(utility['combat_res']) < 3:
            recommendations.append("⚠️ Insufficient Combat Res coverage (need 3+ sources)")
        
        # Performance recommendations
        if performance['active_raiders'] < composition['total'] * 0.8:
            inactive = composition['total'] - performance['active_raiders']
            recommendations.append(f"ℹ️ {inactive} members have no recent raid logs")
        
        excellent = len(performance['performance_tiers']['excellent'])
        total_raiders = performance['active_raiders']
        if total_raiders > 0 and excellent / total_raiders < 0.2:
            recommendations.append("💡 Consider focused training for top performers to reach 95+ percentile")
        
        needs_work = len(performance['performance_tiers']['needs_work'])
        if needs_work > 0:
            recommendations.append(f"📚 {needs_work} members performing below 50th percentile - offer coaching")
        
        inconsistent = len(performance['consistency_analysis']['inconsistent'])
        if inconsistent > 0:
            recommendations.append(f"📊 {inconsistent} members show inconsistent performance - review gameplay patterns")
        
        return recommendations
    
    def generate_raid_comp_suggestion(self, difficulty: str = 'mythic') -> Dict:
        """Generate optimal raid composition for 20-man mythic"""
        comp = {
            'tanks': [],
            'healers': [],
            'melee': [],
            'ranged': []
        }
        
        # Sort by readiness and performance
        sorted_chars = sorted(
            self.characters,
            key=lambda x: (
                x.get('readiness', {}).get('score', 0),
                float(str(x.get('wcl_mythic', {}).get('best_performance', 0)).replace(',', '') or 0)
            ),
            reverse=True
        )
        
        for char in sorted_chars:
            role = char.get('role', 'DPS')
            char_info = {
                'name': char['name'],
                'class': char['class'],
                'spec': char['spec'],
                'readiness': char.get('readiness', {}).get('score', 0),
                'performance': char.get('wcl_mythic', {}).get('best_performance', 0)
            }
            
            if role == 'TANK' and len(comp['tanks']) < 2:
                comp['tanks'].append(char_info)
            elif role == 'HEALING' and len(comp['healers']) < 5:
                comp['healers'].append(char_info)
            elif len(comp['melee']) + len(comp['ranged']) < 13:
                # Check if melee or ranged
                is_melee = any(spec in char['spec'] for spec in self.SPEC_ROLES['Melee'])
                if is_melee and len(comp['melee']) < 7:
                    comp['melee'].append(char_info)
                elif not is_melee and len(comp['ranged']) < 6:
                    comp['ranged'].append(char_info)
        
        return comp
    
    def export_analytics_report(self, output_file: str = "logs/guild_analytics.json"):
        """Export comprehensive analytics report"""
        report = {
            'generated': datetime.now().isoformat(),
            'roster_composition': self.analyze_roster_composition(),
            'utility_coverage': self.check_utility_coverage(),
            'performance_analysis': self.analyze_raid_performance(),
            'recommendations': self.get_roster_recommendations(),
            'suggested_mythic_comp': self.generate_raid_comp_suggestion('mythic')
        }
        
        os.makedirs("logs", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Guild analytics report saved to {output_file}")
        return report


def print_analytics_summary(analytics: GuildAnalytics):
    """Print summary of analytics to console"""
    print("\n" + "="*60)
    print("🏰 GUILD ANALYTICS SUMMARY")
    print("="*60)
    
    comp = analytics.analyze_roster_composition()
    print(f"\n📊 Roster: {comp['total']} members")
    print(f"   Tanks: {comp['by_role']['Tank']} | Healers: {comp['by_role']['Healer']}")
    print(f"   Melee: {comp['by_role']['Melee']} | Ranged: {comp['by_role']['Ranged']}")
    
    perf = analytics.analyze_raid_performance()
    print(f"\n🎯 Active Raiders: {perf['active_raiders']}")
    print(f"   Excellent (95+): {len(perf['performance_tiers']['excellent'])}")
    print(f"   Good (75-94): {len(perf['performance_tiers']['good'])}")
    print(f"   Average (50-74): {len(perf['performance_tiers']['average'])}")
    
    recs = analytics.get_roster_recommendations()
    print(f"\n💡 Recommendations ({len(recs)}):")
    for rec in recs[:5]:
        print(f"   {rec}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    analytics = GuildAnalytics()
    
    if not analytics.characters:
        print("❌ No character data found. Run crawl_enhanced.py first.")
        exit(1)
    
    # Generate and export report
    report = analytics.export_analytics_report()
    
    # Print summary
    print_analytics_summary(analytics)
    
    print("✅ Guild analytics complete!")
    print("📊 Full report: logs/guild_analytics.json")
