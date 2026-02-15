import requests
import json
import matplotlib.pyplot as plt
import matplotlib
import re
from matplotlib.patches import Patch

# Fix for Korean characters in matplotlib
matplotlib.rcParams['axes.unicode_minus'] = False
try:
    plt.rcParams['font.family'] = ['AppleGothic', 'DejaVu Sans']
except:
    pass

# Configuration
ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s"
REPORT_CODE = "Aq2YakZhCGWd9Dvw"  # e.g., "aBcDeFgH123" from warcraftlogs.com/reports/CODE
FIGHT_ID = 48

# Personal cooldowns
PERSONAL_COOLDOWNS = {
    190319: ('Combustion', 10), 12472: ('Icy Veins', 25), 194223: ('Celestial Alignment', 20),
    365350: ('Arcane Surge', 15), 360194: ('Deathmark', 16), 228260: ('Void Eruption', 60),
    107574: ('Avatar', 20), 1719: ('Recklessness', 12), 31884: ('Avenging Wrath', 25),
    231895: ('Crusade', 25), 387184: ('Weapons of Order', 8), 155166: ('Breath of Sindragosa', 15),
    13750: ('Adrenaline Rush', 15), 121471: ('Shadow Blades', 20), 19574: ('Bestial Wrath', 15),
    288613: ('Trueshot', 15), 266779: ('Coordinated Assault', 20), 106951: ('Berserk', 20),
    102560: ('Incarnation', 30), 323764: ('Convoke the Spirits', 4), 114051: ('Ascendance', 15),
    191634: ('Stormkeeper', 15), 265187: ('Summon Demonic Tyrant', 15), 205180: ('Summon Darkglare', 20),
    162264: ('Metamorphosis', 30), 391109: ('Dark Ascension', 20),
    137639: ('Storm, Earth, and Fire', 15), 152173: ('Serenity', 12), 375087: ('Dragonrage', 20),
    1122: ('Summon Infernal', 30),
}

# Raid-wide buffs (show on all players)
RAID_BUFFS = {
    2825: ('Bloodlust', 40), 32182: ('Heroism', 40),
    80353: ('Time Warp', 40), 90355: ('Ancient Hysteria', 40), 390386: ('Fury of the Aspects', 40),
}

# Targeted buffs (show on players who received them)
TARGETED_BUFFS = {
    10060: ('Power Infusion', 20),
}

def graphql_request(query, variables=None):
    """Make a GraphQL request to WCL API"""
    if not ACCESS_TOKEN or ACCESS_TOKEN == "YOUR_ACCESS_TOKEN_HERE":
        raise Exception("Please set ACCESS_TOKEN in the script")
    
    url = "https://www.warcraftlogs.com/api/v2/client"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    
    response = requests.post(url, headers=headers, json={"query": query, "variables": variables or {}})
    
    if response.status_code == 401:
        raise Exception("401 Unauthorized - Create a new token at https://www.warcraftlogs.com/api/clients")
    
    response.raise_for_status()
    data = response.json()
    
    if "errors" in data:
        raise Exception(f"GraphQL Error: {data['errors']}")
    
    return data["data"]

def get_report_data():
    """Fetch report and fight information"""
    query = """
    query ($code: String!) {
      reportData {
        report(code: $code) {
          title
          fights { id name startTime endTime }
          masterData {
            actors(type: "Player") { id name type subType petOwner }
          }
        }
      }
    }
    """
    data = graphql_request(query, {"code": REPORT_CODE})
    return data["reportData"]["report"]

def get_player_data(player_id, fight_id):
    """Get cooldown casts and damage data for a player"""
    query = """
    query ($code: String!, $fightIDs: [Int]!, $sourceID: Int!) {
      reportData {
        report(code: $code) {
          events(fightIDs: $fightIDs, sourceID: $sourceID, dataType: Casts, limit: 10000) {
            data
          }
          damageDone: table(fightIDs: $fightIDs, sourceID: $sourceID, dataType: DamageDone)
        }
      }
    }
    """
    data = graphql_request(query, {"code": REPORT_CODE, "fightIDs": [fight_id], "sourceID": player_id})
    return data["reportData"]["report"]

def get_raid_buffs(fight):
    """Get all raid-wide buff casts for the fight"""
    query = """
    query ($code: String!, $fightIDs: [Int]!) {
      reportData {
        report(code: $code) {
          events(fightIDs: $fightIDs, dataType: Casts, limit: 10000) {
            data
          }
        }
      }
    }
    """
    data = graphql_request(query, {"code": REPORT_CODE, "fightIDs": [fight['id']]})
    events = data["reportData"]["report"]["events"]["data"]
    
    raid_buffs = []
    for event in events:
        if event.get('type') == 'cast':
            ability_id = event.get('abilityGameID')
            if ability_id in RAID_BUFFS:
                cd_name, duration = RAID_BUFFS[ability_id]
                raid_buffs.append({
                    'name': cd_name,
                    'time': event['timestamp'] - fight['startTime'],
                    'duration': duration,
                    'ability_id': ability_id
                })
    
    return raid_buffs

def get_targeted_buffs(player_id, fight):
    """Get targeted buffs received by a specific player"""
    query = """
    query ($code: String!, $fightIDs: [Int]!, $targetID: Int!) {
      reportData {
        report(code: $code) {
          events(fightIDs: $fightIDs, targetID: $targetID, dataType: Buffs, limit: 10000) {
            data
          }
        }
      }
    }
    """
    data = graphql_request(query, {"code": REPORT_CODE, "fightIDs": [fight['id']], "targetID": player_id})
    events = data["reportData"]["report"]["events"]["data"]
    
    targeted_buffs = []
    for event in events:
        if event.get('type') == 'applybuff':
            ability_id = event.get('abilityGameID')
            if ability_id in TARGETED_BUFFS:
                cd_name, duration = TARGETED_BUFFS[ability_id]
                targeted_buffs.append({
                    'name': cd_name,
                    'time': event['timestamp'] - fight['startTime'],
                    'duration': duration,
                    'ability_id': ability_id
                })
    
    return targeted_buffs

def get_dps_timeline(player_id, fight):
    """Get DPS graph data for a player"""
    query = """
    query ($code: String!, $fightIDs: [Int]!, $sourceID: Int!, $startTime: Float!, $endTime: Float!) {
      reportData {
        report(code: $code) {
          graph(
            fightIDs: $fightIDs, 
            sourceID: $sourceID, 
            dataType: DamageDone, 
            startTime: $startTime,
            endTime: $endTime
          )
        }
      }
    }
    """
    data = graphql_request(query, {
        "code": REPORT_CODE, 
        "fightIDs": [fight['id']], 
        "sourceID": player_id,
        "startTime": fight['startTime'],
        "endTime": fight['endTime']
    })
    return data["reportData"]["report"]["graph"]

def format_time(ms):
    """Convert milliseconds to MM:SS format"""
    seconds = ms / 1000
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"

def analyze_player(player, fight, raid_buffs):
    """Analyze a single player's performance"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {player['name']} ({player['subType']} {player['type']})")
    print(f"{'='*60}")
    
    player_data = get_player_data(player['id'], fight['id'])
    
    # Extract personal cooldown casts
    events = player_data.get('events', {}).get('data', [])
    personal_cooldowns = []
    
    for event in events:
        if event.get('type') == 'cast':
            ability_id = event.get('abilityGameID')
            if ability_id in PERSONAL_COOLDOWNS:
                cd_name, duration = PERSONAL_COOLDOWNS[ability_id]
                personal_cooldowns.append({
                    'name': cd_name,
                    'time': event['timestamp'] - fight['startTime'],
                    'duration': duration,
                    'ability_id': ability_id,
                    'type': 'personal'
                })
    
    # Get targeted buffs for this player
    targeted_buffs = get_targeted_buffs(player['id'], fight)
    for buff in targeted_buffs:
        buff['type'] = 'targeted'
    
    # Combine all cooldowns
    cooldowns = personal_cooldowns + targeted_buffs + [
        {**buff, 'type': 'raid'} for buff in raid_buffs
    ]
    cooldowns.sort(key=lambda x: x['time'])
    
    damage_table = player_data.get('damageDone', {}).get('data', {}).get('entries', [])
    total_damage = damage_table[0]['total'] if damage_table else 0
    
    print(f"Total Damage: {total_damage:,}")
    print(f"Cooldowns Used: {len(cooldowns)}")
    
    if cooldowns:
        print("\nCooldown Timeline:")
        for cd in cooldowns:
            cd_type_label = {'personal': '🔵', 'targeted': '🟢', 'raid': '🔴'}[cd['type']]
            print(f"  {format_time(cd['time'])} {cd_type_label} {cd['name']} (duration: {cd['duration']}s)")
    
    # Get DPS timeline
    try:
        graph_data = get_dps_timeline(player['id'], fight)
        
        if 'data' not in graph_data:
            print("⚠️ No DPS data available")
            return
        
        series_data = graph_data['data']
        
        if isinstance(series_data, dict) and 'series' in series_data:
            series = series_data['series']
        elif isinstance(series_data, list):
            series = series_data
        else:
            print("⚠️ Cannot parse DPS data structure")
            return
        
        if not series or len(series) == 0:
            print("⚠️ No DPS series available")
            return
        
        player_series = series[0]
        
        if isinstance(player_series, dict) and 'data' in player_series:
            data_points = player_series['data']
        else:
            print("⚠️ Cannot extract data points")
            return
        
        if len(data_points) <= 2 and all(p == 0 for p in data_points):
            print("⚠️ No DPS data available for this player")
            return
        
        # Build timeline
        point_start = player_series.get('pointStart', 0)
        point_interval = player_series.get('pointInterval', 1000)
        
        timeline = []
        for i, dps_value in enumerate(data_points):
            time_ms = point_start + (i * point_interval) - fight['startTime']
            time_sec = time_ms / 1000
            timeline.append((time_sec, dps_value))
        
        # Calculate DPS during cooldowns
        cd_dps_stats = []
        for cd in cooldowns:
            cd_start = cd['time'] / 1000
            cd_end = cd_start + cd['duration']
            
            cd_dps_values = [dps for time, dps in timeline if cd_start <= time <= cd_end]
            
            if cd_dps_values:
                avg_dps = sum(cd_dps_values) / len(cd_dps_values)
                max_dps = max(cd_dps_values)
                cd_dps_stats.append({
                    'name': cd['name'],
                    'type': cd['type'],
                    'time': format_time(cd['time']),
                    'avg_dps': int(avg_dps),
                    'max_dps': int(max_dps),
                    'duration': cd['duration']
                })
        
        if cd_dps_stats:
            print("\n" + "="*60)
            print("DPS During Cooldowns:")
            print("="*60)
            for stat in cd_dps_stats:
                type_label = {'personal': '🔵', 'targeted': '🟢', 'raid': '🔴'}[stat['type']]
                print(f"{stat['time']} {type_label} {stat['name']} ({stat['duration']}s)")
                print(f"  Average DPS: {stat['avg_dps']:,}")
                print(f"  Peak DPS: {stat['max_dps']:,}")
                print()
        
        # Create plot
        plt.figure(figsize=(16, 8))
        times, dps_values = zip(*timeline)
        plt.plot(times, dps_values, 'purple', linewidth=2, label='DPS', zorder=1)
        
        # Add cooldown windows with different colors
        for cd in cooldowns:
            cd_start = cd['time'] / 1000
            cd_end = cd_start + cd['duration']
            
            if cd['type'] == 'personal':
                color, alpha = 'blue', 0.15
            elif cd['type'] == 'targeted':
                color, alpha = 'green', 0.2
            else:  # raid
                color, alpha = 'red', 0.25
            
            plt.axvspan(cd_start, cd_end, alpha=alpha, color=color, zorder=0)
            plt.axvline(x=cd_start, color=color, linestyle='--', alpha=0.7, linewidth=1.5, zorder=2)
            
            cd_dps = [dps for time, dps in timeline if cd_start <= time <= cd_end]
            if cd_dps:
                peak_dps = max(cd_dps)
                plt.text(cd_start, peak_dps * 1.05, cd['name'], 
                        rotation=45, fontsize=8, color=color, fontweight='bold',
                        verticalalignment='bottom', horizontalalignment='left', zorder=3)
        
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('DPS', fontsize=12)
        plt.title(f"{player['name']}'s DPS Timeline with Cooldown Windows", fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        legend_elements = [
            plt.Line2D([0], [0], color='purple', lw=2, label='DPS'),
            Patch(facecolor='blue', alpha=0.3, label='Personal CDs'),
            Patch(facecolor='green', alpha=0.3, label='Targeted Buffs'),
            Patch(facecolor='red', alpha=0.3, label='Raid Buffs')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        ax = plt.gca()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_time(x * 1000)))
        plt.xticks(rotation=45)
        
        safe_name = re.sub(r'[^\w\s-]', '', player['name']).strip()
        filename = f"Figure/{safe_name}_dps_timeline.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"\n✅ Chart saved as: {filename}")
        plt.close()
        
    except Exception as e:
        print(f"\n⚠️ Could not generate DPS timeline: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("="*60)
    print("Warcraft Logs CD & DPS Analyzer")
    print("="*60)
    
    if REPORT_CODE == "YOUR_REPORT_CODE":
        print("\n❌ ERROR: Please set REPORT_CODE")
        return
    
    try:
        print(f"\nFetching report: {REPORT_CODE}")
        report = get_report_data()
        
        print(f"Report Title: {report['title']}")
        print(f"\nAvailable fights:")
        for fight in report['fights']:
            print(f"  {fight['id']}: {fight['name']}")
        
        fight = next((f for f in report['fights'] if f['id'] == FIGHT_ID), None)
        if not fight:
            print(f"\n❌ Fight {FIGHT_ID} not found!")
            return
        
        print(f"\nAnalyzing Fight {FIGHT_ID}: {fight['name']}")
        
        # Get raid-wide buffs
        print("\nFetching raid-wide buffs...")
        raid_buffs = get_raid_buffs(fight)
        print(f"Found {len(raid_buffs)} raid buff casts")
        
        players = report['masterData']['actors']
        print(f"Found {len(players)} total actors")
        
        # Filter real players
        real_players = [
            p for p in players 
            if p.get('type') != 'Unknown' 
            and not p.get('petOwner')
            and p.get('subType')
        ]
        print(f"Filtered to {len(real_players)} real players")
        
        # Filter DPS players
        dps_players = []
        for player in real_players:
            try:
                player_data = get_player_data(player['id'], fight['id'])
                damage_table = player_data.get('damageDone', {}).get('data', {}).get('entries', [])
                total_damage = damage_table[0]['total'] if damage_table else 0
                if total_damage > 0:
                    dps_players.append(player)
            except:
                pass
        
        print(f"Found {len(dps_players)} players with DPS data")
        
        for player in dps_players:
            try:
                analyze_player(player, fight, raid_buffs)
            except Exception as e:
                print(f"\n⚠️ Error analyzing {player['name']}: {e}")
        
        print("\n" + "="*60)
        print("✅ Analysis complete!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
