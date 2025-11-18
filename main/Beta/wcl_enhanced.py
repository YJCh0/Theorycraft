"""
Enhanced WarcraftLogs API integration with detailed rankings
Add this as: wcl_enhanced.py
"""
import requests
import time
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from functools import lru_cache

class WarcraftLogsAPI:
    """Enhanced WarcraftLogs API client with comprehensive raid data"""
    
    # Current raid tier configuration
    CURRENT_RAIDS = {
        'tww-s1': {
            'id': 38,
            'name': 'Nerub-ar Palace',
            'encounters': [
                'Ulgrax the Devourer', 'The Bloodbound Horror', 'Sikran',
                'Rasha\'kan', 'Broodtwister Ovi\'nax', 'Nexus-Princess Ky\'veza',
                'The Silken Court', 'Queen Ansurek'
            ]
        }
    }
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://www.warcraftlogs.com/api/v2/client"
        self.current_raid = self.CURRENT_RAIDS['tww-s1']
        self.cache_dir = "logs/wcl_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _make_request(self, query: str, variables: dict, retries=3) -> Optional[dict]:
        """Make GraphQL request with retry logic and caching"""
        # Create cache key
        cache_key = f"{variables.get('name', 'guild')}_{variables.get('server', '')}_{hash(query)}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Check cache (valid for 1 hour)
        if os.path.exists(cache_file):
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < 3600:  # 1 hour
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except:
                    pass
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(
                    self.base_url,
                    json={"query": query, "variables": variables},
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get("Retry-After", 60))
                    print(f"⏳ Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if 'errors' in data:
                    print(f"⚠️ GraphQL Error: {data['errors']}")
                    return None
                
                # Cache successful response
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(data, f)
                except:
                    pass
                
                return data
                
            except Exception as e:
                if attempt == retries - 1:
                    print(f"❌ Request failed: {e}")
                    return None
                time.sleep(2 ** attempt)
        
        return None
    
    def get_comprehensive_character_data(self, name: str, server: str, region: str, role: str) -> dict:
        """Get all character raid data - WCL v2 API with fallback"""
        metric = "hps" if role.lower() == "healer" else "dps"
        
        # Try the simpler parses query first (more reliable)
        query = """
        query($name: String!, $server: String!, $region: String!) {
          characterData {
            character(name: $name, serverSlug: $server, serverRegion: $region) {
              name
              classID
            }
          }
        }
        """
        
        variables = {
            "name": name,
            "server": server.lower(),
            "region": region
        }
        
        result = self._make_request(query, variables)
        
        if not result:
            return {}
        
        char_data = result.get('data', {}).get('characterData', {}).get('character')
        if not char_data:
            return {}
        
        # Now get the actual rankings using the simpler query
        # This avoids the complex JSON field issues
        return self._get_rankings_simple(name, server, region, metric, char_data)
    
    def _get_rankings_simple(self, name: str, server: str, region: str, metric: str, char_info: dict) -> dict:
        """Get rankings using multiple simple queries (more reliable)"""
        processed = {
            'name': char_info.get('name'),
            'class_id': char_info.get('classID'),
            'mythic': {},
            'heroic': {},
            'recent_activity': [],
            'has_logs': False
        }
        
        # Query for each encounter individually (more reliable than zoneRankings)
        for encounter_name in self.current_raid['encounters']:
            # For now, use a simpler approach - just get best performance
            pass
        
        # Simplified: Use the REST API style query for now
        # This is more stable than the complex GraphQL queries
        mythic_data = self._get_difficulty_rankings(name, server, region, metric, 5)
        heroic_data = self._get_difficulty_rankings(name, server, region, metric, 4)
        
        if mythic_data or heroic_data:
            processed['has_logs'] = True
            processed['mythic'] = mythic_data
            processed['heroic'] = heroic_data
        
        return processed
    
    def _get_difficulty_rankings(self, name: str, server: str, region: str, metric: str, difficulty: int) -> dict:
        """Get rankings for specific difficulty using correct WCL API"""
        # WCL API v2: encounterRankings doesn't take parameters, returns all as JSON
        query = """
        query($name: String!, $server: String!, $region: String!) {
          characterData {
            character(name: $name, serverSlug: $server, serverRegion: $region) {
              encounterRankings
            }
          }
        }
        """
        
        variables = {
            "name": name,
            "server": server.lower(),
            "region": region
        }
        
        result = self._make_request(query, variables)
        
        if not result:
            return {}
        
        try:
            char_data = result.get('data', {}).get('characterData', {}).get('character', {})
            rankings_json = char_data.get('encounterRankings')
            
            if not rankings_json:
                return {}
            
            # Parse the JSON response
            import json
            all_rankings = json.loads(rankings_json) if isinstance(rankings_json, str) else rankings_json
            
            # Filter for the specific zone and difficulty we want
            filtered_rankings = self._filter_rankings(all_rankings, self.current_raid['id'], difficulty, metric)
            
            return self._process_rankings_json(filtered_rankings)
        except Exception as e:
            print(f"  ⚠️ Error parsing difficulty {difficulty}: {e}")
            return {}
    
    def _filter_rankings(self, all_rankings, zone_id: int, difficulty: int, metric: str) -> dict:
        """Filter rankings for specific zone/difficulty from the full JSON"""
        if not all_rankings or not isinstance(all_rankings, list):
            return {}
        
        # Find rankings for our zone
        for zone_rankings in all_rankings:
            if zone_rankings.get('zone') == zone_id and zone_rankings.get('difficulty') == difficulty:
                # Filter by metric
                if zone_rankings.get('metric') == metric:
                    return zone_rankings
        
        # If exact match not found, try to find any matching zone/difficulty
        for zone_rankings in all_rankings:
            if zone_rankings.get('zone') == zone_id and zone_rankings.get('difficulty') == difficulty:
                return zone_rankings
        
        return {}
    
    def _process_rankings_json(self, rankings_data) -> dict:
        """Process rankings from JSON format"""
        if not rankings_data or not isinstance(rankings_data, dict):
            return {}
        
        result = {
            'best_performance': rankings_data.get('bestPerformanceAverage'),
            'median_performance': rankings_data.get('medianPerformanceAverage'),
            'difficulty': rankings_data.get('difficulty'),
            'boss_rankings': [],
            'all_stars': []
        }
        
        # Process boss rankings - handle multiple possible field names
        rankings = rankings_data.get('ranks', []) or rankings_data.get('rankings', []) or rankings_data.get('encounterRankings', [])
        
        for rank in rankings:
            # Handle both nested and flat encounter structures
            if isinstance(rank.get('encounter'), dict):
                encounter_name = rank['encounter'].get('name', 'Unknown')
                encounter_id = rank['encounter'].get('id', 0)
            else:
                encounter_name = rank.get('encounterName', 'Unknown')
                encounter_id = rank.get('encounterID', 0)
            
            result['boss_rankings'].append({
                'boss': encounter_name,
                'encounter_id': encounter_id,
                'rank_percent': rank.get('rankPercent', 0),
                'median_percent': rank.get('medianPercent', 0),
                'best_amount': rank.get('bestAmount', 0) or rank.get('bestSpec', {}).get('best_amount', 0),
                'total_kills': rank.get('totalKills', 0),
                'fastest_kill': rank.get('fastestKill', 0),
                'locked_in': rank.get('lockedIn', False),
                'today_percent': rank.get('todayPercent', 0),
                'historical_percent': rank.get('historicalPercent', 0),
                'spec': rank.get('spec', 'Unknown'),
                'consistency_score': self._calculate_consistency(
                    rank.get('rankPercent', 0),
                    rank.get('medianPercent', 0)
                )
            })
        
        # Process all-stars - may be in different locations
        all_stars = rankings_data.get('allStars', []) or []
        for star in all_stars:
            result['all_stars'].append({
                'partition': star.get('partition'),
                'spec': star.get('spec'),
                'points': star.get('points', 0),
                'possible': star.get('possiblePoints', 0),
                'rank': star.get('rank', 0),
                'rank_percent': star.get('rankPercent', 0),
                'total': star.get('total', 0)
            })
        
        return result
    
    def _process_rankings(self, rankings: dict) -> dict:
        """Process ranking data for a difficulty (fallback method)"""
        if not rankings:
            return {}
        
        return {
            'best_performance': rankings.get('bestPerformanceAverage'),
            'median_performance': rankings.get('medianPerformanceAverage'),
            'difficulty': rankings.get('difficulty'),
            'boss_rankings': [
                {
                    'boss': r['encounter']['name'],
                    'encounter_id': r['encounter']['id'],
                    'rank_percent': r.get('rankPercent', 0),
                    'median_percent': r.get('medianPercent', 0),
                    'best_amount': r.get('bestAmount', 0),
                    'total_kills': r.get('totalKills', 0),
                    'fastest_kill': r.get('fastestKill', 0),
                    'locked_in': r.get('lockedIn', False),
                    'today_percent': r.get('todayPercent', 0),
                    'historical_percent': r.get('historicalPercent', 0),
                    'spec': r.get('spec', 'Unknown'),
                    'consistency_score': self._calculate_consistency(
                        r.get('rankPercent', 0),
                        r.get('medianPercent', 0)
                    )
                }
                for r in rankings.get('rankings', [])
            ],
            'all_stars': [
                {
                    'partition': s.get('partition'),
                    'spec': s.get('spec'),
                    'points': s.get('points', 0),
                    'possible': s.get('possiblePoints', 0),
                    'rank': s.get('rank', 0),
                    'rank_percent': s.get('rankPercent', 0),
                    'total': s.get('total', 0)
                }
                for s in rankings.get('allStars', [])
            ]
        }
    
    def _process_recent_reports(self, reports: List[dict]) -> List[dict]:
        """Process recent raid reports (currently not available in simple query)"""
        # Note: Recent reports require a different query
        # Simplified for now - can be enhanced later
        return []
    
    def _calculate_consistency(self, best_percent: float, median_percent: float) -> float:
        """Calculate consistency score (0-100, higher is more consistent)"""
        if median_percent == 0 or best_percent == 0:
            return 0
        
        # If median is close to best, player is consistent
        consistency = (median_percent / best_percent) * 100
        return min(100, consistency)
    
    def get_guild_progress(self, guild_name: str, server: str, region: str) -> dict:
        """Get guild's raid progression"""
        query = """
        query($name: String!, $server: String!, $region: String!, $zoneID: Int!) {
          guildData {
            guild(name: $name, serverSlug: $server, serverRegion: $region) {
              name
              zoneRankings(zoneID: $zoneID) {
                progress {
                  encountersDefeated
                  totalEncounters
                }
                difficulty
                metric
                zone {
                  name
                  encounters {
                    id
                    name
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "name": guild_name,
            "server": server.lower(),
            "region": region,
            "zoneID": self.current_raid['id']
        }
        
        result = self._make_request(query, variables)
        
        if not result:
            return {}
        
        guild_data = result.get('data', {}).get('guildData', {}).get('guild')
        return guild_data if guild_data else {}
    
    def get_raid_attendance(self, characters: List[dict]) -> dict:
        """Calculate raid attendance across all characters"""
        total_chars = len(characters)
        active_raiders = 0
        total_activity = []
        
        for char in characters:
            if char.get('recent_activity'):
                active_raiders += 1
                total_activity.extend(char['recent_activity'])
        
        # Group by date
        dates = {}
        for activity in total_activity:
            date = activity['date']
            if date not in dates:
                dates[date] = {'chars': set(), 'kills': 0, 'wipes': 0}
            dates[date]['chars'].add(activity.get('char_name', 'Unknown'))
            dates[date]['kills'] += activity.get('kills', 0)
            dates[date]['wipes'] += activity.get('wipes', 0)
        
        return {
            'total_characters': total_chars,
            'active_raiders': active_raiders,
            'participation_rate': (active_raiders / total_chars * 100) if total_chars > 0 else 0,
            'raid_nights': len(dates),
            'dates': dates
        }


# Helper functions for integration
def format_recent_activity(activity: List[dict]) -> str:
    """Format recent activity for markdown"""
    if not activity:
        return "*No recent raid activity in the last 2 weeks*"
    
    lines = ["### 📅 Recent Raid Activity\n"]
    lines.append("| Date | Duration | Kills | Wipes | Bosses |")
    lines.append("|------|----------|-------|-------|--------|")
    
    for report in activity[:5]:  # Show last 5 raids
        lines.append(
            f"| {report['date']} | "
            f"{report['duration_minutes']:.0f}m | "
            f"{report['kills']} | "
            f"{report['wipes']} | "
            f"{report['bosses_attempted']} |"
        )
    
    return "\n".join(lines)


def analyze_performance_consistency(boss_rankings: List[dict]) -> dict:
    """Analyze player's consistency across bosses"""
    if not boss_rankings:
        return {
            'average_consistency': 0,
            'consistency_rating': 'Unknown',
            'total_bosses': 0
        }
    
    consistency_scores = [b['consistency_score'] for b in boss_rankings]
    avg_consistency = sum(consistency_scores) / len(consistency_scores)
    
    rating = 'Excellent' if avg_consistency >= 90 else \
             'Good' if avg_consistency >= 75 else \
             'Average' if avg_consistency >= 60 else \
             'Inconsistent'
    
    return {
        'average_consistency': avg_consistency,
        'consistency_rating': rating,
        'best_boss': max(boss_rankings, key=lambda x: x['rank_percent'])['boss'],
        'worst_boss': min(boss_rankings, key=lambda x: x['rank_percent'])['boss'],
        'total_bosses': len(boss_rankings)
    }


def calculate_raid_readiness(ilvl: float, mplus_score: float, wcl_avg: float) -> dict:
    """Calculate raid readiness score"""
    # Weights: ilvl (40%), M+ experience (20%), Past performance (40%)
    ilvl_score = max(0, min(100, (ilvl - 615) / 1.15))  # 615-730 range
    mplus_score_normalized = max(0, min(100, mplus_score / 35))  # 0-3500 range
    wcl_score = wcl_avg
    
    readiness = (ilvl_score * 0.4) + (mplus_score_normalized * 0.2) + (wcl_score * 0.4)
    
    rating = 'Mythic Ready' if readiness >= 85 else \
             'Heroic Ready' if readiness >= 70 else \
             'Normal Ready' if readiness >= 50 else \
             'Needs Improvement'
    
    return {
        'score': readiness,
        'rating': rating,
        'components': {
            'ilvl': ilvl_score,
            'mplus': mplus_score_normalized,
            'performance': wcl_score
        }
    }


# Export functions
def save_enhanced_wcl_data(characters: List[dict], output_file: str = "logs/wcl_enhanced.json"):
    """Save enhanced WCL data to JSON"""
    os.makedirs("logs", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(characters, f, indent=2, ensure_ascii=False)
    print(f"✅ Enhanced WCL data saved to {output_file}")
