# 🎮 WoW Guild Dashboard - Enhanced Edition v2.0

## 📋 Implementation Guide

This guide will help you upgrade your WoW guild dashboard with all the new enhanced features.

---

## 🆕 New Features

### 1. **Enhanced WarcraftLogs Integration**
- ✅ Detailed boss rankings (best, median, consistency)
- ✅ Recent raid activity tracking (last 2 weeks)
- ✅ Speed rankings and execution scores
- ✅ All-star rankings per boss
- ✅ Performance consistency analysis

### 2. **Guild Analytics Module**
- ✅ Roster composition analysis
- ✅ Utility coverage checking
- ✅ Performance tier distribution
- ✅ Raid readiness scoring
- ✅ Actionable recommendations

### 3. **Enhanced Dashboard (7 Tabs)**
- 📊 Overview - Guild progress and top improvers
- 📋 Roster - Full character list with readiness scores
- 🎯 Analytics - Performance analysis and recommendations
- 🏆 Raiding - Detailed raid performance with consistency
- 🏔️ M+ - Mythic+ scores and breakdowns
- 🛡️ Composition - Roster balance and suggested comps
- 📈 Trends - Historical progress tracking

### 4. **Raid Readiness System**
- Calculates readiness score based on:
  - Item level (40%)
  - M+ experience (20%)
  - Past raid performance (40%)
- Ratings: Mythic Ready, Heroic Ready, Normal Ready, Needs Improvement

### 5. **Performance Consistency Tracking**
- Tracks consistency across bosses
- Identifies reliable performers
- Flags inconsistent players who need support
- Shows best/worst bosses per character

---

## 📦 Installation Steps

### Step 1: Add New Files

Save these new files in your project directory:

```
your_project/
├── wcl_enhanced.py              # Enhanced WCL API module
├── crawl_enhanced.py            # Enhanced crawler
├── guild_analytics.py           # Guild analytics module
├── generate_dashboard_enhanced.py   # Enhanced dashboard generator
├── run_enhanced.py              # Master runner script
├── (keep all your existing files)
```

### Step 2: Update Your .env File

Make sure your `.env` file has all required credentials:

```env
# Blizzard API
BLIZZARD_CLIENT_ID=your_client_id
BLIZZARD_CLIENT_SECRET=your_client_secret

# WarcraftLogs API
WCL_ACCESS_TOKEN=your_wcl_token

# Region Settings
REGION=kr
NAMESPACE=profile-kr

# Optional: Discord Integration
DISCORD_WEBHOOK_URL=your_webhook_url

# Optional: Public Dashboard URL
DASHBOARD_URL=https://your-dashboard-url.com
```

### Step 3: Install Dependencies (if needed)

```bash
pip install requests python-dotenv rich
```

---

## 🚀 Usage

### Method 1: Run Enhanced Pipeline (Recommended)

Run everything with one command:

```bash
python run_enhanced.py
```

This will:
1. ✅ Crawl all character data with enhanced WCL
2. ✅ Update historical tracking
3. ✅ Fetch M+ details
4. ✅ Run guild analytics
5. ✅ Post to Discord (if configured)
6. ✅ Generate enhanced dashboard

### Method 2: Run Individual Modules

Run specific modules as needed:

```bash
# Enhanced crawler only
python crawl_enhanced.py

# Guild analytics only
python guild_analytics.py

# Dashboard only
python generate_dashboard_enhanced.py
```

---

## 📊 Understanding the New Features

### Raid Readiness Score

Each character gets a readiness score (0-100):

- **85-100**: Mythic Ready 🟢
- **70-84**: Heroic Ready 🟡
- **50-69**: Normal Ready 🟠
- **0-49**: Needs Improvement 🔴

**Formula:**
```
Readiness = (ilvl_score × 0.4) + (mplus_score × 0.2) + (wcl_score × 0.4)
```

### Consistency Analysis

Measures how consistent a player performs:

- **Excellent (90%+)**: Player consistently performs well
- **Good (75-89%)**: Generally reliable with occasional variance
- **Average (60-74%)**: Noticeable variance between pulls
- **Inconsistent (<60%)**: Needs coaching/support

**Formula:**
```
Consistency = (median_parse / best_parse) × 100
```

### Guild Analytics Recommendations

The system provides actionable recommendations:

- ⚠️ **Warnings**: Critical issues (missing tanks, healers, utilities)
- ℹ️ **Info**: Important notices (inactive raiders, performance gaps)
- 💡 **Tips**: Improvement suggestions (training opportunities)

---

## 📁 Output Files

### Generated Files

| File | Description |
|------|-------------|
| `dashboard.html` | Main enhanced dashboard (7 tabs) |
| `logs/Player_data.csv` | Character summary data |
| `logs/characters_enhanced.json` | Full enhanced character data |
| `logs/guild_analytics.json` | Guild analytics report |
| `logs/mplus_enhanced.json` | Detailed M+ run data |
| `logs/wcl_cache/*.json` | WCL API response cache |
| `detailed/*.md` | Individual character reports |

### Character Report Structure

Each `detailed/{name}.md` now includes:

```markdown
# Character Name

## 📊 Overview
- Item Level, M+, WCL scores
- **Raid Readiness**: Score and rating
- **Consistency**: Rating and analysis

## ⚔️ Equipment
- All items with upgrade levels

## 📅 Recent Activity
- Last 2 weeks of raids
- Kills, wipes, duration

## 🏆 Mythic Performance
- Boss rankings with consistency scores
- Best/median/speed rankings

## 🏆 Heroic Performance
- Boss rankings

## ⭐ All Stars Points
```

---

## 🔧 Customization

### Adjust Readiness Weights

Edit `wcl_enhanced.py`:

```python
def calculate_raid_readiness(ilvl, mplus_score, wcl_avg):
    # Change these weights as desired
    ilvl_weight = 0.4      # Item level importance
    mplus_weight = 0.2     # M+ experience importance
    wcl_weight = 0.4       # Past performance importance
    
    readiness = (ilvl_score * ilvl_weight) + 
                (mplus_normalized * mplus_weight) + 
                (wcl_score * wcl_weight)
```

### Change Current Raid Tier

Edit `wcl_enhanced.py`:

```python
CURRENT_RAIDS = {
    'tww-s1': {
        'id': 38,  # Change this to new raid ID
        'name': 'Nerub-ar Palace',
        'encounters': [...]  # Update boss list
    }
}
```

### Add Custom Analytics

Edit `guild_analytics.py` and add your own analysis functions:

```python
def your_custom_analysis(self):
    # Your custom logic here
    pass
```

---

## 🐛 Troubleshooting

### Issue: "No enhanced character data found"

**Solution:** Run `crawl_enhanced.py` first to generate the data:
```bash
python crawl_enhanced.py
```

### Issue: "WCL API rate limited"

**Solution:** The system has built-in rate limiting and caching. Wait a few minutes and try again. Cache files in `logs/wcl_cache/` are valid for 1 hour.

### Issue: "Some characters have no consistency data"

**Reason:** Characters with no raid logs or only 1 boss kill don't have enough data for consistency analysis. This is expected.

### Issue: Dashboard missing some features

**Solution:** Make sure all required data files exist:
- `logs/Player_data.csv`
- `logs/characters_enhanced.json`
- `logs/guild_analytics.json`

Run the full pipeline: `python run_enhanced.py`

---

## 📈 Best Practices

### 1. **Run Daily**

Set up a daily cron job or scheduled task:

```bash
# Linux/Mac cron
0 9 * * * cd /path/to/project && python run_enhanced.py

# Windows Task Scheduler
# Create task to run run_enhanced.py daily at 9 AM
```

### 2. **Monitor API Limits**

- Blizzard API: Very generous limits
- WarcraftLogs: ~100 requests per hour for free tier
- Raider.IO: No official limit, but be respectful

### 3. **Review Analytics Weekly**

Check `logs/guild_analytics.json` weekly for:
- Roster balance issues
- Performance trends
- Missing utilities
- Improvement opportunities

### 4. **Share with Guild**

Host the `dashboard.html` on:
- GitHub Pages (free)
- Netlify (free)
- Your own web server

Update `DASHBOARD_URL` in `.env` to share the link in Discord.

---

## 🎯 Next Steps

### After Initial Setup:

1. ✅ Run `python run_enhanced.py` for first data collection
2. ✅ Review the analytics report in `logs/guild_analytics.json`
3. ✅ Check the dashboard for any issues
4. ✅ Share dashboard with officers for feedback
5. ✅ Set up automated daily runs

### Weekly Tasks:

1. Review top improvers and celebrate progress
2. Check recommendations and take action
3. Monitor consistency scores for struggling players
4. Update raid composition based on suggestions
5. Track historical trends for long-term planning

---

## 📞 Support

If you encounter issues:

1. Check the console output for error messages
2. Verify all API credentials in `.env`
3. Check that `characters.csv` is properly formatted
4. Review the troubleshooting section above
5. Check log files in `logs/` directory

---

## 🎉 Congratulations!

You now have a fully enhanced WoW guild dashboard with:

- ✨ Comprehensive WarcraftLogs integration
- ✨ Intelligent raid readiness scoring
- ✨ Performance consistency tracking
- ✨ Guild-wide analytics and recommendations
- ✨ Beautiful 7-tab interactive dashboard
- ✨ Historical trend tracking
- ✨ Discord integration

**Happy raiding! 🏆**

---

## 📝 Version History

### v2.0 - Enhanced Edition
- Added enhanced WCL API integration
- Added guild analytics module
- Added raid readiness scoring
- Added consistency tracking
- Upgraded to 7-tab dashboard
- Added roster composition analysis
- Added actionable recommendations

### v1.0 - Original
- Basic character crawling
- Simple dashboard with 5 tabs
- M+ and WCL basic integration
