# 🎮 WoW Guild Dashboard - Complete Setup Guide

## 📋 What's New

Your dashboard now includes:
1. **📈 Weekly Trend Charts** - Track guild progress over time
2. **🏆 Top Improvers Leaderboard** - See who's grinding the hardest
3. **📢 Discord Integration** - Auto-post updates and milestones
4. **🏔️ M+ Dungeon Breakdown** - Detailed dungeon performance by character

---

## 🚀 Quick Start

### Step 1: Update Your .env File

Add Discord webhook URL to your `.env` file:

```env
# Existing credentials
BLIZZARD_CLIENT_ID=your_client_id
BLIZZARD_CLIENT_SECRET=your_client_secret
WCL_ACCESS_TOKEN=your_wcl_token
REGION=kr
NAMESPACE=profile-kr

# NEW: Discord Integration (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

**How to get Discord Webhook:**
1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Name it "WoW Guild Bot"
5. Copy the Webhook URL

### Step 2: Install New Dependencies

```bash
pip install requests python-dotenv
```

### Step 3: Run the Master Script

Instead of running individual scripts, use the master runner:

```bash
python run_all.py
```

This will:
- ✅ Crawl character data
- ✅ Update historical tracking
- ✅ Fetch M+ dungeon details
- ✅ Post to Discord
- ✅ Generate dashboard

---

## 📂 New File Structure

```
your_project/
├── characters.csv              # Your character list
├── .env                        # API credentials + Discord webhook
├── wow_crawler.py             # Your existing crawler (renamed)
├── dashboard_generator.py     # Your existing dashboard (renamed)
├── history_tracker.py         # NEW: Track progress over time
├── discord_integration.py     # NEW: Discord webhook posting
├── mplus_breakdown.py         # NEW: Detailed M+ analysis
├── run_all.py                 # NEW: Master script (run this!)
├── logs/
│   ├── Player_data.csv        # Current character data
│   ├── history.json           # Historical snapshots (auto-created)
│   ├── milestones.json        # Milestone tracking (auto-created)
│   └── mplus_breakdown.json   # M+ dungeon data (auto-created)
└── dashboard.html             # Your beautiful dashboard!
```

---

## 🎯 Features Explained

### 1. 📈 Weekly Trend Charts

The dashboard now shows a line chart tracking:
- Average guild ilvl over time
- Average M+ score over time
- Average WCL performance over time

**How it works:**
- Every time you run the crawler, a snapshot is saved
- The dashboard displays all snapshots as a trend line
- Keeps last 30 days of data

**To see trends:**
- Run the crawler daily/weekly
- After 2+ runs, trends will appear

### 2. 🏆 Top Improvers

Shows who improved the most in the last 7 days:
- ilvl gains
- M+ score gains
- WCL parse improvements

**Formula:**
```
Improvement Score = (ilvl gain × 2) + (M+ gain × 0.01) + (WCL gain × 0.5)
```

### 3. 📢 Discord Integration

Automatically posts to Discord:
- **Daily Summary** - Guild stats snapshot
- **Top Improvers** - Weekly leaderboard
- **Milestones** - Celebrates achievements

**Milestones tracked:**
- ilvl 720, 725
- M+ score 3000, 3500
- WCL parse 99, 100

**To test Discord:**
```bash
python discord_integration.py
```

### 4. 🏔️ M+ Dungeon Breakdown

Shows each character's best key for every dungeon:
- Key level (+10, +12, etc.)
- Timed (✅) or depleted (❌)
- Color-coded by difficulty

**To fetch M+ data:**
```bash
python mplus_breakdown.py
```

---

## 🔧 Usage

### Daily/Weekly Update

Just run one command:
```bash
python run_all.py
```

### Manual Steps (if needed)

```bash
# 1. Crawl character data
python wow_crawler.py

# 2. Add to history
python -c "from history_tracker import add_current_snapshot; add_current_snapshot()"

# 3. Fetch M+ data (optional, takes longer)
python mplus_breakdown.py

# 4. Post to Discord (optional)
python discord_integration.py

# 5. Generate dashboard
python dashboard_generator.py
```

---

## 📊 Dashboard Features

Your dashboard now includes:

### Top Section
- 📊 Total Members
- ⚔️ Average ilvl
- 🏔️ Average M+ Score
- 📈 Average WCL

### Charts
1. **Guild Progress Trends** - Multi-line chart showing progress over time
2. **Top Improvers Table** - 🥇🥈🥉 rankings with gains
3. **Item Level Distribution** - Bar chart by character
4. **M+ Score Distribution** - Bar chart by character
5. **WCL Performance** - Bar chart by character

### Character Table
- Click any character name for detailed stats
- Spec icons displayed inline
- Color-coded badges for scores

---

## 🤖 Automation (Optional)

### Schedule Daily Updates

**On Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\run_all.py`

**On Linux/Mac (cron):**
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 6 AM)
0 6 * * * cd /path/to/project && python run_all.py
```

---

## 🐛 Troubleshooting

### "No historical data yet"
- Run the crawler at least twice on different days
- Check if `logs/history.json` exists

### Discord not posting
- Verify webhook URL in `.env`
- Test with: `python discord_integration.py`
- Check Discord server permissions

### M+ data missing
- Raider.IO may not have data for all characters
- Some characters may not have done M+ this season
- This is normal and non-critical

### Trends not showing
- You need at least 2 data points (2 different days)
- Run the crawler again tomorrow

---

## 💡 Tips

1. **Run daily** for best trend tracking
2. **Discord webhook** works best in a dedicated channel
3. **M+ data fetch** is slowest part (skippable if needed)
4. **History keeps 30 days** - older data auto-deleted
5. **Milestones only fire once** - won't spam Discord

---

## 🎉 What's Next?

You now have:
- ✅ Historical trend tracking
- ✅ Top improvers leaderboard
- ✅ Discord integration
- ✅ M+ dungeon breakdown

Possible future enhancements:
- Email reports
- Raid boss analysis
- Attendance tracking
- Character comparison tools
- Mobile app

---

## 📞 Support

If you run into issues:
1. Check the console output for errors
2. Verify all API credentials in `.env`
3. Make sure files are in correct locations
4. Test each script individually

---

**Happy raiding! 🎮⚔️**
