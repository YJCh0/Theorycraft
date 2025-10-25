import discord
from discord import app_commands
from discord.ext import commands
from warcraft_api import (
    get_ilvl,
    get_raiderio_score,
    get_warcraftlogs_data,
    get_guild_summary
)
from config import DISCORD_TOKEN

# ───────────────────────────────
# 기본 설정
# ───────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ───────────────────────────────
# 클래스별 색상 테마 (Embed 컬러)
# ───────────────────────────────
CLASS_COLORS = {
    "Death Knight": 0xC41E3A,
    "Demon Hunter": 0xA330C9,
    "Druid": 0xFF7C0A,
    "Evoker": 0x33937F,
    "Hunter": 0xAAD372,
    "Mage": 0x3FC7EB,
    "Monk": 0x00FF98,
    "Paladin": 0xF48CBA,
    "Priest": 0xFFFFFF,
    "Rogue": 0xFFF468,
    "Shaman": 0x0070DD,
    "Warlock": 0x8788EE,
    "Warrior": 0xC69B6D,
}

# ───────────────────────────────
# 역할별 이모티콘
# ───────────────────────────────
ROLE_ICONS = {
    "tank": "🛡️",
    "healer": "✚",
    "dps": "⚔️"
}

# ───────────────────────────────
# 봇이 실행될 때
# ───────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Slash Commands Synced: {len(synced)}개")
    except Exception as e:
        print(f"❌ Sync 실패: {e}")


# ───────────────────────────────
# /logs — 캐릭터 로그 조회
# ───────────────────────────────
@bot.tree.command(name="logs", description="WoW 캐릭터의 로그, M+ 점수, 아이템 레벨을 조회합니다.")
@app_commands.describe(
    server="서버 이름 (예: azshara)",
    character="캐릭터 이름 (예: 용불타)",
    role="역할 (tank / dps / healer)",
    wow_class="클래스 (예: Mage, Paladin, Druid 등)"
)
async def logs(interaction: discord.Interaction, server: str, character: str, role: str, wow_class: str):
    await interaction.response.defer(thinking=True)

    # API 호출
    logs = get_warcraftlogs_data(server, character, role)
    ilvl = get_ilvl(server, character)
    mplus = get_raiderio_score(server, character)

    if "error" in logs:
        await interaction.followup.send(f"⚠️ 오류 발생: {logs['error']}")
        return

    # 역할 이모티콘 & 클래스 색상
    role_icon = ROLE_ICONS.get(role.lower(), "❓")
    embed_color = CLASS_COLORS.get(wow_class.title(), 0x7289DA)

    avg = logs.get("bestPerformanceAverage", "N/A")
    rankings = logs.get("rankings", [])

    embed = discord.Embed(
        title=f"{role_icon} {character} ({wow_class}) — {server}",
        description=f"**아이템 레벨:** `{ilvl}`\n"
                    f"**Mythic+ 점수:** `{mplus}`\n"
                    f"**WCL 평균:** `{avg}`",
        color=embed_color
    )
    embed.set_footer(text=f"Role: {role.capitalize()} | Data from WarcraftLogs & Raider.io")

    # 상위 5개 보스 정보
    for boss in rankings[:5]:
        embed.add_field(
            name=f"⚔️ {boss['encounter']['name']}",
            value=f"Rank: `{boss.get('rankPercent', 0):.2f}%` / `{boss.get('outOf', 0)}명`\n"
                  f"Best: `{boss.get('bestAmount', 0)}`",
            inline=False
        )

    await interaction.followup.send(embed=embed)


# ───────────────────────────────
# /compare — 두 캐릭터 비교
# ───────────────────────────────
@bot.tree.command(name="compare", description="두 캐릭터의 WCL 평균 점수를 비교합니다.")
@app_commands.describe(
    server="서버 이름",
    char1="첫 번째 캐릭터",
    char2="두 번째 캐릭터",
    role="역할 (dps / healer / tank)"
)
async def compare(interaction: discord.Interaction, server: str, char1: str, char2: str, role: str):
    await interaction.response.defer(thinking=True)

    logs1 = get_warcraftlogs_data(server, char1, role)
    logs2 = get_warcraftlogs_data(server, char2, role)

    if "error" in logs1 or "error" in logs2:
        await interaction.followup.send("⚠️ 데이터 로드 중 오류가 발생했습니다.")
        return

    avg1 = logs1.get("bestPerformanceAverage", 0)
    avg2 = logs2.get("bestPerformanceAverage", 0)

    winner = char1 if avg1 > avg2 else char2
    color = 0x00FF00 if avg1 > avg2 else 0xFF0000

    embed = discord.Embed(
        title="🏆 캐릭터 비교 결과",
        description=f"**{char1}:** {avg1}\n"
                    f"**{char2}:** {avg2}\n\n"
                    f"🔥 더 높은 성능: **{winner}**",
        color=color
    )
    await interaction.followup.send(embed=embed)


# ───────────────────────────────
# /mplus — M+ 점수 단독 조회
# ───────────────────────────────
@bot.tree.command(name="mplus", description="Raider.io에서 M+ 점수만 조회합니다.")
@app_commands.describe(server="서버", character="캐릭터 이름")
async def mplus(interaction: discord.Interaction, server: str, character: str):
    await interaction.response.defer(thinking=True)
    score = get_raiderio_score(server, character)
    await interaction.followup.send(f"📊 **{character}**의 Mythic+ 점수: `{score}`")


# ───────────────────────────────
# /ilvl — 아이템 레벨 단독 조회
# ───────────────────────────────
@bot.tree.command(name="ilvl", description="공식 사이트에서 캐릭터의 아이템 레벨을 조회합니다.")
@app_commands.describe(server="서버", character="캐릭터 이름")
async def ilvl(interaction: discord.Interaction, server: str, character: str):
    await interaction.response.defer(thinking=True)
    ilvl = get_ilvl(server, character)
    await interaction.followup.send(f"🧱 **{character}**의 아이템 레벨: `{ilvl}`")


# ───────────────────────────────
# /guild_summary — 길드 평균 로그 조회
# ───────────────────────────────
@bot.tree.command(name="guild_summary", description="길드 전체의 평균 로그 성능을 조회합니다.")
@app_commands.describe(guild_name="길드 이름", server="서버")
async def guild_summary(interaction: discord.Interaction, guild_name: str, server: str):
    await interaction.response.defer(thinking=True)
    summary = get_guild_summary(guild_name, server)

    if "error" in summary:
        await interaction.followup.send(f"⚠️ 오류 발생: {summary['error']}")
        return

    avg = summary.get("bestPerformanceAverage", "N/A")
    embed = discord.Embed(
        title=f"🏰 {guild_name} 길드 — {server}",
        description=f"💫 평균 로그 성능: `{avg}`",
        color=0x3498db
    )
    await interaction.followup.send(embed=embed)


from discord import app_commands
import discord

# ───────────────────────────────
# 서버 / 클래스 / 역할 리스트
# ───────────────────────────────
KOREAN_SERVERS = [
    "azshara", "burning-legion", "durotan", "stormrage",
    "zuljin", "hakkar", "rexxar", "dalaran", "cenarius"
]

WOW_CLASSES = [
    "Death Knight", "Demon Hunter", "Druid", "Evoker", "Hunter",
    "Mage", "Monk", "Paladin", "Priest", "Rogue",
    "Shaman", "Warlock", "Warrior"
]

ROLES = ["Tank", "Healer", "DPS"]

# ───────────────────────────────
# 자동완성 함수
# ───────────────────────────────

@logs.autocomplete("server")
async def server_autocomplete(interaction: discord.Interaction, current: str):
    """서버 자동완성"""
    return [
        app_commands.Choice(name=server.title(), value=server)
        for server in KOREAN_SERVERS if current.lower() in server.lower()
    ][:10]


@logs.autocomplete("wow_class")
async def class_autocomplete(interaction: discord.Interaction, current: str):
    """클래스 자동완성"""
    return [
        app_commands.Choice(name=cls, value=cls)
        for cls in WOW_CLASSES if current.lower() in cls.lower()
    ][:10]


@logs.autocomplete("role")
async def role_autocomplete(interaction: discord.Interaction, current: str):
    """역할 자동완성"""
    return [
        app_commands.Choice(name=role, value=role.lower())
        for role in ROLES if current.lower() in role.lower()
    ]

# ───────────────────────────────
# 봇 실행
# ───────────────────────────────
bot.run(DISCORD_TOKEN)

