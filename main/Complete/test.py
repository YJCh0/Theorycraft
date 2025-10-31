import csv
import re
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.theme import Theme

# ───────────────────────────────
# Settings
INPUT_FILE = "characters.csv"
OUTPUT_DIR = "logs"
DETAIL_DIR = "detailed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Player_data.csv")
PREVIOUS_FILE = os.path.join(OUTPUT_DIR, "previous_Player_data.csv")
WEEKLY_FILE = os.path.join(OUTPUT_DIR, "weekly_comparison.csv")
FAILED_LOG = os.path.join(OUTPUT_DIR, "failed_characters.log")

BLIZZARD_CLIENT_ID = "21d80d19190544d0bbe39c06c8af635d"
BLIZZARD_CLIENT_SECRET = "tEHJW0IkA76jRj680UVZ4hfqwaAB5JPp"
ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhMDJlMTcxZC1iY2IzLTQyNDQtOWEwMy1lZDQ1ZDZkNTRmZTgiLCJqdGkiOiI3MjY2ZDU1YmU3NzYyZDk2MWE5ZWY2M2ZiMjEzY2NkM2NkZmI3MTllMDg0NGE2ZDMyODllMWJlMmFhMDhlNmJkMmIzZGNiY2FiMzliYzUzMCIsImlhdCI6MTc2MTE5ODM0OS4zMDkyMzQsIm5iZiI6MTc2MTE5ODM0OS4zMDkyMzcsImV4cCI6MTc5MjMwMjM0OS4zMDEzMzksInN1YiI6IiIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.WQIHgbfjPaWSWp-1EhSyZeL9HYGgYAXtDB3EUIBR5FVlluN193QLDmIfl3V_qIZbwRzHUqoRCrJKQc_FBL5r5crp01X_k05kDuKG-HeZFJgcObZI7kKf5aii4Qn-Hm3I4hdSQ_uiNjvzLg88jMYRFgb2xQ0t8kH-ZfU01tKodV3_tnAxSE-zXoInbIdW_3-RqvFY1tLzvE_eZOPmFD-kVA6WqhyXOGfTnmGhcV-EKwqW2pl0fVUCpyMjsNeVSRh6olnSmuFL5DgLmqbX46VVW6MqFpIN-MxFvft7F6EK-VrTj6vCALFrizxhAaid5vzvRxmUlo-9rn8pFnRjOxzSAWliOknS31nquKXVdvnG4Gdi6AEXRvYWg__Y-couc8qXS1_1GyziWtXJLEGNg8LD-0NDQHDhSczALEoVmt6fQR0jS6KKrZvnt-oE_DDfIlvdsFJp7XP1GlbjlJUvjDRcRaTEPNdJJR7Rp4f6V_I460gU7kJyqwSZ1j7PGiHKFhvfZwgaGhCJ4P7QopLRvo2bRWlu8bjHeabHgzvL1bggKmEQdqQM6GlUleW5xEHkALFbfHVgXUPuhGvRTniPRTIVfE5xP4JLdjcMT_ssExzD6mimR8MV2ZZhdboo--IYmv1TssSZMrbdwJ-CX2fYhi9qqvbKgDyXRr2QwuMgUsXuv5s'
REGION = "kr"

theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "error": "bold red",
    "warning": "yellow"
})
console = Console(theme=theme)

# ────────────────────────────────────────────────
def get_blizzard_token():
    url = f"https://{REGION}.battle.net/oauth/token"
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, data=data, auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET))
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ Blizzard 토큰 발급 실패: {response.status_code}")
        return None
# ───────────────────────────────
# Utility
def safe_request(method, url, retries=3, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, timeout=15, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            if attempt == retries:
                console.print(f"[error]❌ Request failed: {url} ({e})[/error]")
                return None
            time.sleep(2)

def format_num(value, digits=1):
    if not value or value == "N/A": return "None"
    try:
        return f"{float(value):,.{digits}f}"
    except: return str(value)

def format_int(value):
    if not value or value == "N/A": return "None"
    try:
        return f"{int(round(float(value))):,}"
    except: return str(value)

def format_rank(value):
    if not value: return "N/A"
    try:
        return f"{int(value):,}"
    except: return str(value)

# ───────────────────────────────
# Blizzard / Raider.io / WCL API
def get_ilvl(server, character):
    url = f"https://{REGION}.api.blizzard.com/profile/wow/character/{realm}/{character_name}/equipment"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": NAMESPACE, "locale": "ko_KR"}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {character_name} 장비 정보 조회 성공")
        return data
    else:
        print(f"❌ API 요청 실패: {response.status_code} - {response.text}")
        return None

def get_mplus_score(server, character):
    url = "https://raider.io/api/v1/characters/profile"
    params = {
        "region": REGION,
        "realm": server,
        "name": character,
        "fields": "mythic_plus_scores_by_season:current"
    }
    resp = safe_request("GET", url, params=params)
    if not resp: return "N/A"
    data = resp.json()
    seasons = data.get("mythic_plus_scores_by_season", [])
    for s in seasons:
        if "season-tww-3" in s.get("season", ""):
            return s.get("scores", {}).get("all", "N/A")
    return "N/A"

def get_wcl_data(server, character, role):
    url = "https://www.warcraftlogs.com/api/v2/client"
    metric_type = "hps" if role.lower() == "healer" else "dps"
    query = f"""
    {{
      characterData {{
        character(name: "{character}", serverSlug: "{server}", serverRegion: "kr") {{
          name
          zoneRankings(metric: {metric_type})
        }}
      }}
    }}
    """
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    resp = safe_request("POST", url, json={"query": query}, headers=headers)
    if not resp: return None
    try:
        return resp.json()["data"]["characterData"]["character"]
    except Exception:
        return None

# ───────────────────────────────
# Wcl Summary
def format_wcl_log(char, char_class, wcl_spec, wcl, role):
    lines = []
    lines.append("WarcraftLogs Summary for")
    lines.append(f"  {char}")
    lines.append(f"  {wcl_spec} {char_class}\n")

    lines.append(f"Best Performance Average: {format_num(wcl.get('bestPerformanceAverage'))}\n")

    # Best Performances
    lines.append("Best Performances:")
    rankings = wcl.get("zoneRankings", [])
    if rankings:
        for e in rankings:
            boss = e.get("encounter", {}).get("name", "Unknown")
            score = e.get("rankPercent")
            lines.append(f"  {boss}, Score: {format_num(score)}")
    else:
        lines.append("  Cannot find Best Performances")
    lines.append("")

    # All Stars
    lines.append("All Stars Points:")
    stars = wcl.get("allStars", [])
    if stars:
        for s in stars:
            lines.append(
                f"  Partition {s.get('partition')} | Spec: {s.get('spec')} | Points: {format_num(s.get('points'))}/{format_num(s.get('possiblePoints'))} | Rank %: {format_num(s.get('rankPercent'))}"
            )
    else:
        lines.append("  Cannot find All Stars Points")
    lines.append("")

    # Boss DPS/HPS
    lines.append("\nBoss HPS Percentage:" if role.lower()=="healer" else "\nBoss DPS Percentage:")
    if rankings:
        for e in rankings:
            boss = e.get("encounter", {}).get("name", "Unknown")
            rank = e.get("rankPercent")
            best = e.get("bestAmount", 0)
            lines.append(f"  {boss}: Rank {format_num(rank)}%, Best {'HPS' if role.lower()=='healer' else 'DPS'} {format_int(best)}")
    else:
        lines.append("  Cannot find Boss Rankings")

    # Rankings
    lines.append("\nRankings:")
    if stars:
        for s in stars:
            lines.append(
                f"  Partition {s.get('partition')} | Spec: {s.get('spec')} | Rank: {format_rank(s.get('rank'))} / {format_rank(s.get('total'))} | Region: {format_rank(s.get('regionRank'))} | Server: {format_rank(s.get('serverRank'))}"
            )
    else:
        lines.append("  Cannot find Rankings")

    return "\n".join(lines)

# ───────────────────────────────
# Worker
def crawl_character(row, attempt=1):
    server, name, role, cls = row["Server"], row["ID"], row["Role"], row["Class"]
    console.print(f"[info]▶ Fetching {name} (Attempt {attempt})[/info]")

    ilvl = get_ilvl(server, name)
    mplus = get_mplus_score(server, name)
    wcl = get_wcl_data(server, name, role)

    if not wcl and attempt < 3:
        time.sleep(2)
        return crawl_character(row, attempt + 1)
    if not wcl:
        console.print(f"[error]❌ {name} data missing[/error]")
        with open(FAILED_LOG, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
        return [name, cls, "N/A", 0, "N/A", "N/A"]

    spec = wcl.get("activeSpec", {}).get("name", "Unknown")
    log_text = format_wcl_log(name, cls, spec, wcl, role)

    os.makedirs(DETAIL_DIR, exist_ok=True)
    with open(os.path.join(DETAIL_DIR, f"{name}.md"), "w", encoding="utf-8") as f:
        f.write(log_text)

    best_perf = wcl.get("bestPerformanceAverage") or 0
    console.print(f"[success]✔ {name} ({spec} {cls}, ilvl {ilvl})[/success]")
    return [name, cls, spec, ilvl, format_num(mplus), format_num(best_perf)]

# ───────────────────────────────
# Summary & Weekly Comparison
def print_console_summary(results):
    table = Table(title="WoW Character Summary", show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Class", style="magenta")
    table.add_column("Spec", style="yellow")
    table.add_column("ilvl", justify="right", style="green")
    table.add_column("M+", justify="right", style="blue")
    table.add_column("WCL", justify="right", style="red")

    il, mp, wc = 0, 0, 0
    for r in results:
        table.add_row(*[str(x) for x in r])
        try: il += int(r[3]); mp += float(r[4].replace(",", "")); wc += float(r[5].replace(",", ""))
        except: pass
    console.print(table)

    if len(results):
        console.print(f"[info]Average ilvl: {il/len(results):.1f} | M+: {mp/len(results):.1f} | WCL: {wc/len(results):.1f}[/info]")

def generate_weekly_comparison():
    if not os.path.exists(OUTPUT_FILE): return
    if not os.path.exists(PREVIOUS_FILE): return
    cur = {r["ID"]: r for r in csv.DictReader(open(OUTPUT_FILE, encoding="utf-8"))}
    prev = {r["ID"]: r for r in csv.DictReader(open(PREVIOUS_FILE, encoding="utf-8"))}
    with open(WEEKLY_FILE, "w", newline="", encoding="utf-8") as f:
        fields = ["ID","Class","Spec","ilvl","Δilvl","M+","ΔM+","WCL","ΔWCL"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for cid,c in cur.items():
            p = prev.get(cid,{})
            w.writerow({
                "ID": cid, "Class": c["Class"], "Spec": c["Spec"],
                "ilvl": c["ilvl"], "Δilvl": int(c["ilvl"])-int(p.get("ilvl",c["ilvl"])),
                "M+": c["M+"], "ΔM+": float(c["M+"].replace(",",""))-float(p.get("M+",c["M+"]).replace(",","")),
                "WCL": c["WCL"], "ΔWCL": float(c["WCL"])-float(p.get("WCL",c["WCL"]))
            })
    console.print(f"[success]✅ Weekly comparison saved![/success]")

# ───────────────────────────────
# Main
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chars = list(csv.DictReader(open(INPUT_FILE, encoding="utf-8")))
    results = []

    with Progress(SpinnerColumn(), BarColumn(), TextColumn("{task.description} {task.completed}/{task.total}"), console=console) as prog:
        task = prog.add_task("Fetching...", total=len(chars))
        with ThreadPoolExecutor(max_workers=5) as pool:
            for res in pool.map(crawl_character, chars):
                if res: results.append(res)
                prog.update(task, advance=1)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["ID","Class","Spec","ilvl","M+","WCL"], *results])
    console.print(f"[success]✅ Saved to {OUTPUT_FILE}[/success]")

    print_console_summary(results)
    generate_weekly_comparison()

if __name__ == "__main__":
    main()

