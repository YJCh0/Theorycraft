# 🎮 WoW Guild Dashboard - Complete Setup Guide

## 🆕 What's New - Unified Dashboard!

Your dashboard is now a **single file with 4 tabs**:

### 📊 **Tab 1: Overview**
- 📈 Guild progress trends over time
- 🏆 Top improvers leaderboard (last 7 days)

### 📈 **Tab 2: Charts**  
- Item level distribution
- M+ score distribution
- WCL performance

### 🏔️ **Tab 3: M+ Details**
- Detailed view of best M+ runs
- Party composition for each run
- Affixes with emojis
- Timing information
- Direct links to Raider.IO
- **Shows upgrade levels (+2, +3, etc.)**
- **Full party roster with roles**

### 📋 **Tab 4: Roster**
- Complete character list with clickable names
- Spec icons
- Performance badges

---

## 🚀 Quick Start

### Generate Complete Dashboard

```bash
python test_unified_dashboard.py
```

This will:
1. ✅ Fetch enhanced M+ data (with party info)
2. ✅ Generate unified dashboard with tabs
3. ✅ Create single dashboard.html file

Then open **dashboard.html** in your browser!

---

## 📂 File Structure

```
your_project/
├── dashboard.html              # 🆕 Single unified dashboard!
├── test_unified_dashboard.py   # 🆕 Easy test script
├── mplus_enhanced.py           # 🆕 Enhanced M+ with party info
├── history_tracker.py          # Track progress
├── discord_integration.py      # Discord webhooks
├── run_all.py                  # Master runner
└── logs/
    ├── Player_data.csv
    ├── history.json
    └── mplus_enhanced.json     # 🆕 Detailed M+ data
```

---

## 🎯 M+ Details Tab Features

### What You'll See:

**For Each Character:**
- Avatar/thumbnail from Raider.IO
- Class, spec, ilvl
- Total M+ score

**For Each Best Run (Top 5):**

```
#1 Ara-Kara, City of Echoes        +12 +2
✅ Timed | Score: 145.2

🔮 Xal'atath's Bargain | 👑 Tyrannical | 💥 Bursting

⏱️ Clear Time: 28:45
🎯 Par Time: 32:00
📊 Difference: -3:15

Party Composition:
🛡️ 전사잠탱이 - Protection Warrior
💚 리쉽 - Restoration Druid
⚔️ 냥꾼린츠 - Marksmanship Hunter
⚔️ 만보먹고 - Frost Mage
⚔️ 보라발굽 - Destruction Warlock

📊 View on Raider.IO
```

### Key Improvements:
- ✅ **Upgrade levels now visible** (+2, +3 for timed runs)
- ✅ **Full party roster displayed** with names, specs, roles
- ✅ **Role icons**: 🛡️ Tank, 💚 Healer, ⚔️ DPS
- ✅ **Color-coded by difficulty**: 🟢 Low → 🟣 Medium → 🟠 High
- ✅ **Timing details**: Shows if over/under time
- ✅ **Affix emojis**: Easy to see at a glance

---

## 📢 Discord Integration with Dashboard Link

Add to your `.env`:

```env
# Discord webhook (required for notifications)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_URL

# Dashboard public URL (optional - adds clickable link)
DASHBOARD_URL=https://your-site.com/dashboard.html
```

Discord messages will now include a **clickable link** to your dashboard!

---

## 🔧 Usage

### Daily/Weekly Update

```bash
# Option 1: Everything at once
python test_unified_dashboard.py

# Option 2: Step by step
python mplus_enhanced.py          # Fetch detailed M+ data
python history_tracker.py         # Update trends
python generate_html_dashboard.py # Generate dashboard
```

### Just Update M+ Details

```bash
python mplus_enhanced.py
python generate_html_dashboard.py
```

---

## 🎨 Dashboard Navigation

The dashboard has **4 tabs** at the top:

1. **📊 Overview** - Click to see trends and improvers
2. **📈 Charts** - Click to see all distribution charts
3. **🏔️ M+ Details** - Click to see detailed run information
4. **📋 Roster** - Click to see full character list

**Tips:**
- Tabs animate smoothly when switching
- Each tab remembers scroll position
- Click character names in Roster tab for detailed stats

---

## 🐛 Troubleshooting

### "No party members showing"
- **Fixed!** The enhanced version now properly extracts party roster
- Make sure you run `python mplus_enhanced.py` to regenerate data

### "Upgrade level not showing"
- **Fixed!** Now displays "+2", "+3" for timed keys
- Shows "❌" for depleted (no upgrade)

### "Tabs not working"
- Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
- Check browser console for JavaScript errors

### "M+ tab is empty"
- Run `python mplus_enhanced.py` first
- Characters need to have done M+ keys this season
- Check that `logs/mplus_enhanced.json` exists

---

## 🎯 What's Different from Before?

### Old Setup:
- ❌ Two separate HTML files
- ❌ Had to open multiple pages
- ❌ M+ didn't show party members
- ❌ No upgrade levels visible

### New Setup:
- ✅ Single dashboard.html file
- ✅ Everything in tabs
- ✅ Full party roster with roles
- ✅ Upgrade levels displayed
- ✅ Better organized
- ✅ Easier to navigate

---

## 📊 Example Output

When you open **dashboard.html**, you'll see:

```
⚔️ Guild Performance Dashboard

[📊 Overview] [📈 Charts] [🏔️ M+ Details] [📋 Roster]
     ↑ Click to switch tabs

Currently viewing: Overview
- Guild trends chart
- Top 5 improvers with medals 🥇🥈🥉
```

Switch to **M+ Details** tab:
```
Character: 전사잠탱이
Protection Warrior | ilvl 720 | M+ Score: 2,850

#1 Ara-Kara +12 +2 ✅
   Party: Tank, Healer, 3 DPS (all names visible)
   
#2 Grim Batol +11 +1 ✅
   Party: Tank, Healer, 3 DPS (all names visible)
```

---

## 💡 Pro Tips

1. **Bookmark the tabs**: Each tab has its own content
2. **Share the M+ tab**: Perfect for showing off your best runs
3. **Click Raider.IO links**: Goes directly to the run details
4. **Check party comp**: See who you run keys with most
5. **Use Discord link**: Share dashboard with guild via Discord

---

## 🎉 Summary

You now have a **professional-looking unified dashboard** with:
- ✅ Single file, multiple tabs
- ✅ Full M+ details with party members
- ✅ Upgrade levels visible
- ✅ Beautiful UI with smooth transitions
- ✅ Discord integration with dashboard link
- ✅ All features in one place!

**Happy raiding! 🎮⚔️**

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
