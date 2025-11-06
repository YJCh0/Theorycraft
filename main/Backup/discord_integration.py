import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

def send_discord_message(content="", embeds=None):
    """Send a message to Discord via webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ No Discord webhook URL configured")
        return False
    
    payload = {
        "content": content,
        "username": "WoW Guild Bot",
        "avatar_url": "https://wow.zamimg.com/images/wow/icons/large/achievement_guildperk_mobilebanking.jpg"
    }
    
    if embeds:
        payload["embeds"] = embeds
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print("✅ Discord message sent successfully")
            return True
        else:
            print(f"❌ Discord webhook failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending Discord message: {e}")
        return False

def post_guild_summary(total_chars, avg_ilvl, avg_mplus, avg_wcl, dashboard_url=None):
    """Post guild summary statistics"""
    
    description = f"Daily snapshot for {datetime.now().strftime('%Y-%m-%d')}"
    if dashboard_url:
        description += f"\n\n[📊 View Full Dashboard]({dashboard_url})"
    
    embed = {
        "title": "⚔️ Guild Performance Update",
        "description": description,
        "color": 0x667eea,
        "fields": [
            {
                "name": "👥 Total Members",
                "value": str(total_chars),
                "inline": True
            },
            {
                "name": "⚔️ Average ilvl",
                "value": f"{avg_ilvl:.1f}",
                "inline": True
            },
            {
                "name": "🏔️ Average M+ Score",
                "value": f"{avg_mplus:.1f}",
                "inline": True
            },
            {
                "name": "📈 Average WCL",
                "value": f"{avg_wcl:.1f}",
                "inline": True
            }
        ],
        "footer": {
            "text": "두부킴의 유기견들"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return send_discord_message(embeds=[embed])

def post_top_improvers(improvers):
    """Post top improvers to Discord"""
    if not improvers:
        return
    
    description = ""
    for i, player in enumerate(improvers[:5], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        description += f"\n{medal} **{player['name']}** ({player['spec']} {player['class']})\n"
        description += f"   ilvl: +{player['ilvl_gain']:.1f} | M+: +{player['mplus_gain']:.0f} | WCL: +{player['wcl_gain']:.1f}\n"
    
    embed = {
        "title": "🏆 Top Improvers - Last 7 Days",
        "description": description,
        "color": 0xFFD700,
        "footer": {
            "text": "Keep up the great work!"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return send_discord_message(embeds=[embed])

def post_milestone(character_name, milestone_type, value):
    """Post milestone achievement"""
    milestone_messages = {
        "ilvl_720": f"🎉 **{character_name}** reached **720 item level**!",
        "ilvl_725": f"🎊 **{character_name}** hit **725 item level**!",
        "mplus_3000": f"🏔️ **{character_name}** achieved **3000 M+ rating**!",
        "mplus_3500": f"⛰️ **{character_name}** reached **3500 M+ rating**! What a legend!",
        "wcl_99": f"📈 **{character_name}** parsed **99+ on WarcraftLogs**!",
        "wcl_100": f"💯 **{character_name}** got a **perfect 100 parse**! 🔥"
    }
    
    message = milestone_messages.get(milestone_type, f"🎉 {character_name} achieved something awesome!")
    
    embed = {
        "title": "🎯 Milestone Achieved!",
        "description": message,
        "color": 0xFF6B6B,
        "thumbnail": {
            "url": "https://wow.zamimg.com/images/wow/icons/large/achievement_boss_lichking.jpg"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return send_discord_message(embeds=[embed])

def check_and_post_milestones(csv_file="logs/Player_data.csv"):
    """Check for milestones and post to Discord"""
    import csv
    
    if not os.path.exists(csv_file):
        return
    
    # Load previous milestones
    milestones_file = "logs/milestones.json"
    if os.path.exists(milestones_file):
        with open(milestones_file, 'r') as f:
            achieved_milestones = json.load(f)
    else:
        achieved_milestones = {}
    
    new_milestones = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char_name = row['ID']
            
            if char_name not in achieved_milestones:
                achieved_milestones[char_name] = []
            
            # Check ilvl milestones
            try:
                ilvl = float(row['ilvl'])
                if ilvl >= 725 and 'ilvl_725' not in achieved_milestones[char_name]:
                    new_milestones.append((char_name, 'ilvl_725', ilvl))
                    achieved_milestones[char_name].append('ilvl_725')
                elif ilvl >= 720 and 'ilvl_720' not in achieved_milestones[char_name]:
                    new_milestones.append((char_name, 'ilvl_720', ilvl))
                    achieved_milestones[char_name].append('ilvl_720')
            except:
                pass
            
            # Check M+ milestones
            try:
                mplus = float(str(row['M+']).replace(',', ''))
                if mplus >= 3500 and 'mplus_3500' not in achieved_milestones[char_name]:
                    new_milestones.append((char_name, 'mplus_3500', mplus))
                    achieved_milestones[char_name].append('mplus_3500')
                elif mplus >= 3000 and 'mplus_3000' not in achieved_milestones[char_name]:
                    new_milestones.append((char_name, 'mplus_3000', mplus))
                    achieved_milestones[char_name].append('mplus_3000')
            except:
                pass
            
            # Check WCL milestones
            try:
                wcl = float(str(row['WCL']).replace(',', ''))
                if wcl == 100 and 'wcl_100' not in achieved_milestones[char_name]:
                    new_milestones.append((char_name, 'wcl_100', wcl))
                    achieved_milestones[char_name].append('wcl_100')
                elif wcl >= 99 and 'wcl_99' not in achieved_milestones[char_name]:
                    new_milestones.append((char_name, 'wcl_99', wcl))
                    achieved_milestones[char_name].append('wcl_99')
            except:
                pass
    
    # Post new milestones
    for char_name, milestone_type, value in new_milestones:
        post_milestone(char_name, milestone_type, value)
    
    # Save updated milestones
    os.makedirs("logs", exist_ok=True)
    with open(milestones_file, 'w') as f:
        json.dump(achieved_milestones, f, indent=2)
    
    if new_milestones:
        print(f"✅ Posted {len(new_milestones)} new milestones to Discord")
    else:
        print("ℹ️ No new milestones to post")

if __name__ == "__main__":
    print("🤖 Discord Integration Test\n")
    
    # Test basic message
    send_discord_message("🎮 Bot is online and ready!")
    
    # Check for milestones
    check_and_post_milestones()
