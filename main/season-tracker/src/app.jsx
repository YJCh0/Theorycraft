import React, { useState, useEffect } from "react";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 🖼️  게임 로고 이미지 — 여기에 파일을 import 하세요
//
//   1) 이미지 파일을 src/assets/logos/ 폴더에 넣기
//      예: src/assets/logos/d4.png
//
//   2) 아래 주석을 해제하고 경로를 맞춰주세요:
//
import d4Logo   from "./assets/logos/d4.png";
import d2Logo   from "./assets/logos/d2.png";
import poe1Logo from "./assets/logos/poe1.png";
import poe2Logo from "./assets/logos/poe2.png";
import wowLogo  from "./assets/logos/wow.png";
import hsLogo   from "./assets/logos/hs.png";
import sc2Logo  from "./assets/logos/sc2.png";
import ow2Logo  from "./assets/logos/ow2.png";
//
//   3) 각 게임 데이터의 logo 필드에 변수를 넣어주세요:
//      logo: d4Logo,
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const GAMES = [
  // ── Diablo IV ───────────────────────────────────────
  {
    id: "d4",
    name: "Diablo IV",
    shortName: "D4",
    icon: "💀",
    logo: d4Logo,             // ← d4Logo
    accentColor: "#c0392b",
    glowColor: "rgba(192,57,43,0.35)",
    bgColor: "#1a0a0a",
    patch: "v3.0.4",
    label: "S13 · Season of Reckoning",
    startDate: new Date("2026-04-28T00:00:00Z"),
    endDate: new Date("2026-07-20T21:00:00Z"),
    endIsEstimate: true,
    roadmapLabel: "시즌 로드맵",
    items: [
      {
        id: "d4-s13",
        name: "Season of Reckoning",
        sub: "Season 13",
        icon: "💀",
        startDate: new Date("2026-04-28T00:00:00Z"),
        endDate: new Date("2026-07-20T21:00:00Z"),
        endIsEstimate: true,
        note: "Lord of Hatred 확장팩 · War Plans 시스템",
      },
      {
        id: "d4-s14",
        name: "Season 14",
        sub: "다음 시즌",
        icon: "❓",
        startDate: null,
        endDate: null,
        endIsEstimate: false,
        note: "이름·날짜 미발표",
      },
    ],
  },

  // ── Diablo II Resurrected ────────────────────────────
  {
    id: "d2r",
    name: "Diablo II: Resurrected",
    shortName: "D2R",
    icon: "💎",
    logo: d2Logo,             // ← d2Logo
    accentColor: "#8b0000",
    glowColor: "rgba(139,0,0,0.4)",
    bgColor: "#120000",
    patch: "v3.2.0",
    label: "Ladder Season 14",
    startDate: new Date("2026-05-22T01:00:00Z"),
    endDate: null,
    endIsEstimate: false,
    roadmapLabel: "래더 시즌 로드맵",
    items: [
      {
        id: "d2r-s13",
        name: "Ladder Season 13",
        sub: "Reign of the Warlock",
        icon: "🧙",
        startDate: new Date("2026-02-20T01:00:00Z"),
        endDate: new Date("2026-05-22T01:00:00Z"),
        endIsEstimate: false,
        note: "신규 Warlock 클래스 · 패치 v3.1",
      },
      {
        id: "d2r-s14",
        name: "Ladder Season 14",
        sub: "현재 시즌",
        icon: "💎",
        startDate: new Date("2026-05-22T01:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "패치 v3.2 · Terror Zone 개편 · Sunder Charm 조정",
      },
      {
        id: "d2r-s15",
        name: "Ladder Season 15",
        sub: "다음 시즌",
        icon: "❓",
        startDate: null,
        endDate: null,
        endIsEstimate: false,
        note: "날짜 미발표 · 3~4개월 주기 예상",
      },
    ],
  },

  // ── Path of Exile ────────────────────────────────────
  {
    id: "poe1",
    name: "Path of Exile",
    shortName: "PoE1",
    icon: "🔮",
    logo: poe1Logo,             // ← poe1Logo
    accentColor: "#8e44ad",
    glowColor: "rgba(142,68,173,0.35)",
    bgColor: "#0e0813",
    patch: "v3.28",
    label: "3.28 · Mirage",
    startDate: new Date("2026-03-06T21:00:00Z"),
    endDate: new Date("2026-07-20T20:00:00Z"),
    endIsEstimate: false,
    roadmapLabel: "리그 로드맵",
    items: [
      {
        id: "poe1-328",
        name: "Mirage",
        sub: "3.28 리그",
        icon: "🔮",
        startDate: new Date("2026-03-06T21:00:00Z"),
        endDate: new Date("2026-07-20T20:00:00Z"),
        endIsEstimate: false,
        note: "Djinn·Wish 메커닉, Reliquarian",
      },
      {
        id: "poe1-329",
        name: "3.29 리그",
        sub: "다음 리그",
        icon: "⚡",
        startDate: new Date("2026-07-24T20:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "7월 24일 출시 확정 · 이름 미발표",
      },
    ],
  },

  // ── Path of Exile 2 ──────────────────────────────────
  {
    id: "poe2",
    name: "Path of Exile 2",
    shortName: "PoE2",
    icon: "⚗️",
    logo: poe2Logo,             // ← poe2Logo
    accentColor: "#e67e22",
    glowColor: "rgba(230,126,34,0.35)",
    bgColor: "#110d05",
    patch: "v0.5.0",
    label: "0.5.0 · Return of the Ancients",
    startDate: new Date("2026-05-29T20:00:00Z"),
    endDate: null,
    endIsEstimate: false,
    roadmapLabel: "리그 로드맵",
    items: [
      {
        id: "poe2-050",
        name: "Return of the Ancients",
        sub: "0.5.0 리그",
        icon: "⚗️",
        startDate: new Date("2026-05-29T20:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "Runes of Aldur · 2개 신규 직업",
      },
      {
        id: "poe2-100",
        name: "1.0 정식 출시",
        sub: "Early Access 종료",
        icon: "🌟",
        startDate: null,
        endDate: null,
        endIsEstimate: false,
        note: "날짜 미발표 · 2026년 말 예상",
      },
    ],
  },

  // ── World of Warcraft ────────────────────────────────
  {
    id: "wow",
    name: "World of Warcraft",
    shortName: "WoW",
    icon: "⚔️",
    logo: wowLogo,             // ← wowLogo
    accentColor: "#3498db",
    glowColor: "rgba(52,152,219,0.35)",
    bgColor: "#050e1a",
    patch: "v12.0.7",
    label: "Midnight S1 — Revelations",
    startDate: new Date("2026-03-17T15:00:00Z"),
    endDate: null,
    endIsEstimate: false,
    roadmapLabel: "레이드 로드맵",
    items: [
      {
        id: "wow-voidspire",
        name: "The Voidspire",
        sub: "S1 레이드 1 · 6보스",
        icon: "🌑",
        startDate: new Date("2026-03-17T15:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "Xal'atath 직접 대면",
      },
      {
        id: "wow-dreamrift",
        name: "The Dreamrift",
        sub: "S1 레이드 2 · 1보스",
        icon: "🌌",
        startDate: new Date("2026-03-17T15:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "Chimaerus, the Undreamt God",
      },
      {
        id: "wow-quel",
        name: "March on Quel'Danas",
        sub: "S1 레이드 3 · 2보스",
        icon: "🌅",
        startDate: new Date("2026-03-31T15:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "Sunwell 수호 · 12.0.7 Revelations",
      },
      {
        id: "wow-venomous",
        name: "The Venomous Abyss",
        sub: "S2 레이드 · 8보스",
        icon: "🐍",
        startDate: null,
        endDate: null,
        endIsEstimate: false,
        note: "12.1 Curse of Ula'tek · 날짜 미확정",
      },
    ],
  },

  // ── Hearthstone ──────────────────────────────────────
  {
    id: "hs",
    name: "Hearthstone",
    shortName: "HS",
    icon: "🃏",
    logo: hsLogo,             // ← hsLogo
    accentColor: "#f1c40f",
    glowColor: "rgba(241,196,15,0.3)",
    bgColor: "#13100a",
    patch: "v32.x",
    label: "Year of the Scarab",
    startDate: new Date("2026-03-17T00:00:00Z"),
    endDate: null,
    endIsEstimate: false,
    roadmapLabel: "확장팩 로드맵",
    items: [
      {
        id: "hs-cataclysm",
        name: "CATACLYSM",
        sub: "1번째 확장팩",
        icon: "🔥",
        startDate: new Date("2026-03-17T00:00:00Z"),
        endDate: new Date("2026-07-07T17:00:00Z"),
        endIsEstimate: false,
        note: "Herald · Shatter · Colossal · Deathwing",
      },
      {
        id: "hs-violet",
        name: "Escape from Violet Hold",
        sub: "2번째 확장팩",
        icon: "🔓",
        startDate: new Date("2026-07-07T17:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "Prepare · Rulebreaker · Vanessa VanCleef",
      },
      {
        id: "hs-exp3",
        name: "3번째 확장팩",
        sub: "Year of the Scarab",
        icon: "❓",
        startDate: null,
        endDate: null,
        endIsEstimate: false,
        note: "날짜·이름 미발표",
      },
    ],
  },

  // ── StarCraft II ─────────────────────────────────────
  {
    id: "sc2",
    name: "StarCraft II",
    shortName: "SC2",
    icon: "🚀",
    logo: sc2Logo,             // ← sc2Logo
    accentColor: "#00aaff",
    glowColor: "rgba(0,170,255,0.3)",
    bgColor: "#020d1a",
    patch: "v5.0.16",
    label: "2026 Season 2 래더",
    startDate: new Date("2026-06-22T00:00:00Z"),
    endDate: null,
    endIsEstimate: false,
    roadmapLabel: "패치 로드맵",
    items: [
      {
        id: "sc2-5015",
        name: "Patch 5.0.15",
        sub: "2026 Season 1 래더",
        icon: "🛸",
        startDate: new Date("2026-01-15T00:00:00Z"),
        endDate: new Date("2026-06-22T00:00:00Z"),
        endIsEstimate: false,
        note: "GSL Season 1·2 진행 · Legacy of the Void",
      },
      {
        id: "sc2-5016",
        name: "Patch 5.0.16",
        sub: "현재 패치 · 2026 Season 2",
        icon: "🚀",
        startDate: new Date("2026-06-22T00:00:00Z"),
        endDate: null,
        endIsEstimate: false,
        note: "시작 일꾼 12→8 · Warpgate 개편 · 최대 밸런스 패치",
      },
      {
        id: "sc2-next",
        name: "다음 패치",
        sub: "Season 3 예정",
        icon: "❓",
        startDate: null,
        endDate: null,
        endIsEstimate: false,
        note: "날짜 미발표",
      },
    ],
  },

  // ── Overwatch 2 ──────────────────────────────────────
  {
    id: "ow2",
    name: "Overwatch 2",
    shortName: "OW2",
    icon: "🎯",
    logo: ow2Logo,             // ← ow2Logo
    accentColor: "#f97316",
    glowColor: "rgba(249,115,22,0.3)",
    bgColor: "#0f0800",
    patch: "v16.x",
    label: "Reign of Talon S3 · Into the Tiger's Den",
    startDate: new Date("2026-06-16T18:00:00Z"),
    endDate: new Date("2026-08-10T18:00:00Z"),
    endIsEstimate: false,
    roadmapLabel: "시즌 로드맵",
    items: [
      {
        id: "ow2-s1",
        name: "S1: Conquest",
        sub: "Reign of Talon 시즌 1",
        icon: "⚡",
        startDate: new Date("2026-02-10T18:00:00Z"),
        endDate: new Date("2026-04-14T18:00:00Z"),
        endIsEstimate: false,
        note: "신규 히어로 5명 동시 출시 · 스토리 아크 시작",
      },
      {
        id: "ow2-s2",
        name: "S2: Summit",
        sub: "Reign of Talon 시즌 2",
        icon: "🏔️",
        startDate: new Date("2026-04-14T18:00:00Z"),
        endDate: new Date("2026-06-16T18:00:00Z"),
        endIsEstimate: false,
        note: "신규 히어로 Sierra · Operation Grand Mesa",
      },
      {
        id: "ow2-s3",
        name: "S3: Into the Tiger's Den",
        sub: "Reign of Talon 시즌 3 · 현재",
        icon: "🎯",
        startDate: new Date("2026-06-16T18:00:00Z"),
        endDate: new Date("2026-08-10T18:00:00Z"),
        endIsEstimate: false,
        note: "신규 히어로 Shion · Anima Strike 이벤트",
      },
      {
        id: "ow2-s4",
        name: "Season 4",
        sub: "다음 시즌",
        icon: "❓",
        startDate: null,
        endDate: null,
        endIsEstimate: false,
        note: "날짜 미발표 · 8월 예상",
      },
    ],
  },
];

// ━━━ 유틸 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function daysBetween(a, b) { return Math.floor((b - a) / 86400000); }
function calcProgress(start, end, now) {
  if (!start || !end) return null;
  return Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100));
}
function elapsedText(days) {
  if (days <= 0) return "시작 전";
  if (days < 7) return `${days}일째`;
  const w = Math.floor(days / 7), r = days % 7;
  return r === 0 ? `${w}주째` : `${w}주 ${r}일째`;
}
function daysLeftText(days) {
  if (days < 0) return "종료됨";
  if (days === 0) return "오늘 종료";
  if (days === 1) return "내일 종료";
  return `${days}일 남음`;
}
function kfmt(d, opts) { return d.toLocaleDateString("ko-KR", opts); }
function urgencyColor(days) {
  if (days < 14) return "#e74c3c";
  if (days < 30) return "#e67e22";
  return "rgba(255,255,255,0.4)";
}

// ━━━ SVG 링 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function Ring({ pct, color, size = 72, strokeWidth = 4 }) {
  const r = (size - strokeWidth * 2) / 2;
  const c = 2 * Math.PI * r;
  const offset = pct == null ? c : c - (pct / 100) * c;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)", flexShrink: 0 }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={strokeWidth} />
      {pct != null && (
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease" }} />
      )}
    </svg>
  );
}

// ━━━ 링 중앙 (이모지 or 이미지) ━━━━━━━━━━━━━━━━━━━━━━━
function RingCenter({ logo, icon, size }) {
  if (logo) {
    return <img src={logo} alt="" style={{ width: size * 0.52, height: size * 0.52, objectFit: "contain", borderRadius: 4 }} />;
  }
  return <span style={{ fontSize: size * 0.3 }}>{icon}</span>;
}

// ━━━ % 뱃지 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function PctBadge({ pct, color }) {
  return (
    <div style={{
      position: "absolute", bottom: -8, left: "50%", transform: "translateX(-50%)",
      fontSize: 9, fontWeight: 800, fontFamily: "monospace",
      color: "#fff", background: color,
      borderRadius: 4, padding: "1px 5px", whiteSpace: "nowrap",
    }}>
      {Math.round(pct)}%
    </div>
  );
}

// ━━━ 뱃지 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function Badge({ text, color, dim }) {
  return (
    <span style={{
      fontSize: 8, fontWeight: 800, letterSpacing: 0.5,
      borderRadius: 3, padding: "1px 5px", flexShrink: 0,
      color: dim ? "rgba(255,255,255,0.4)" : color,
      background: dim ? "rgba(255,255,255,0.08)" : color + "33",
    }}>{text}</span>
  );
}

// ━━━ 로드맵 아이템 행 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function ItemRow({ item, now, color }) {
  const unknown  = !item.startDate;
  const upcoming = !unknown && now < item.startDate;
  const active   = !unknown && now >= item.startDate && (!item.endDate || now < item.endDate);
  const done     = !unknown && item.endDate && now >= item.endDate;

  const pct     = calcProgress(item.startDate, item.endDate, now);
  const elapsed = !unknown ? daysBetween(item.startDate, now) : null;
  const left    = item.endDate ? daysBetween(now, item.endDate) : null;
  const until   = upcoming ? daysBetween(now, item.startDate) : null;
  const ringColor = active ? color : "rgba(255,255,255,0.2)";

  return (
    <div style={{
      background: active ? "rgba(255,255,255,0.05)" : "rgba(255,255,255,0.02)",
      border: `1px solid ${active ? color + "44" : "rgba(255,255,255,0.06)"}`,
      borderRadius: 10, padding: "10px 12px",
      display: "flex", alignItems: "center", gap: 10,
    }}>
      <div style={{ position: "relative", width: 44, height: 44, flexShrink: 0 }}>
        <Ring pct={done ? 100 : active ? pct : null} color={ringColor} size={44} strokeWidth={3} />
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15 }}>
          {item.icon}
        </div>
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: active ? "#f0f0f0" : "rgba(255,255,255,0.32)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {item.name}
          </span>
          {active   && <Badge text="LIVE" color={color} />}
          {upcoming && <Badge text="SOON" dim />}
        </div>
        <div style={{ fontSize: 10, color: "rgba(255,255,255,0.28)", marginBottom: 3 }}>
          {item.sub}
          {item.note && <span style={{ color: "rgba(255,255,255,0.18)" }}> · {item.note}</span>}
        </div>
        {unknown ? (
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.22)" }}>일정 미발표</span>
        ) : upcoming ? (
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.5)" }}>
            {kfmt(item.startDate, { month: "long", day: "numeric" })} 출시 · D-{until}
          </span>
        ) : done ? (
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.22)" }}>종료됨</span>
        ) : (
          <div style={{ display: "flex", gap: 8, fontSize: 10 }}>
            <span style={{ color: "rgba(255,255,255,0.5)" }}>{elapsedText(elapsed)}</span>
            {left != null
              ? <span style={{ color: urgencyColor(left) }}>· {daysLeftText(left)}{item.endIsEstimate ? " (추정)" : ""}</span>
              : <span style={{ color: "rgba(255,255,255,0.28)" }}>· 종료일 미발표</span>
            }
          </div>
        )}
      </div>

      {active && pct != null && (
        <span style={{ fontSize: 10, fontWeight: 800, fontFamily: "monospace", color: "#fff", background: color, borderRadius: 4, padding: "2px 5px", flexShrink: 0 }}>
          {Math.round(pct)}%
        </span>
      )}
    </div>
  );
}

// ━━━ 게임 카드 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function GameCard({ game, now, open, onToggle }) {
  const current = game.items.find(
    i => i.startDate && now >= i.startDate && (!i.endDate || now < i.endDate)
  );

  const elapsed = daysBetween(game.startDate, now);
  const left    = game.endDate ? daysBetween(now, game.endDate) : null;
  const dispPct = current
    ? calcProgress(current.startDate, current.endDate, now)
    : calcProgress(game.startDate, game.endDate, now);
  const dispIcon = current ? current.icon : game.icon;
  const dispName = current ? current.name : game.label;

  return (
    <div onClick={onToggle} style={{
      background: `linear-gradient(135deg, ${game.bgColor} 0%, #0d0d0d 100%)`,
      border: `1px solid ${open ? game.accentColor + "66" : "rgba(255,255,255,0.07)"}`,
      borderRadius: 16, padding: open ? "20px" : "16px",
      cursor: "pointer", transition: "all 0.3s ease",
      boxShadow: open ? `0 0 32px ${game.glowColor}, 0 4px 24px rgba(0,0,0,0.5)` : "0 2px 12px rgba(0,0,0,0.4)",
      position: "relative", overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 2,
        background: `linear-gradient(90deg,transparent,${game.accentColor},transparent)`,
        opacity: open ? 1 : 0.4, transition: "opacity 0.3s",
      }} />

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ position: "relative", width: 72, height: 82, flexShrink: 0 }}>
          <Ring pct={dispPct} color={game.accentColor} size={72} strokeWidth={4} />
          <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 10, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <RingCenter logo={game.logo} icon={dispIcon} size={72} />
          </div>
          {dispPct != null && <PctBadge pct={dispPct} color={game.accentColor} />}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
            <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: 1.5, color: game.accentColor, textTransform: "uppercase", fontFamily: "'Courier New',monospace" }}>
              {game.shortName}
            </span>
            {game.patch && (
              <span style={{ fontSize: 9, background: game.accentColor + "22", color: game.accentColor, borderRadius: 4, padding: "1px 5px", fontFamily: "monospace" }}>
                {game.patch}
              </span>
            )}
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#f0f0f0", marginBottom: 4, lineHeight: 1.3, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {dispName}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12, flexWrap: "wrap" }}>
            {current ? (
              <>
                <span style={{ color: "rgba(255,255,255,0.5)" }}>{elapsedText(daysBetween(current.startDate, now))}</span>
                {current.endDate
                  ? <span style={{ color: urgencyColor(daysBetween(now, current.endDate)) }}>
                      · {daysLeftText(daysBetween(now, current.endDate))}{current.endIsEstimate ? " (추정)" : ""}
                    </span>
                  : <span style={{ color: "rgba(255,255,255,0.3)" }}>· 종료일 미발표</span>
                }
              </>
            ) : (
              <>
                <span style={{ color: "rgba(255,255,255,0.5)" }}>{elapsedText(elapsed)}</span>
                {left != null
                  ? <span style={{ color: urgencyColor(left) }}>· {daysLeftText(left)}{game.endIsEstimate ? " (추정)" : ""}</span>
                  : <span style={{ color: "rgba(255,255,255,0.3)" }}>· 종료일 미발표</span>
                }
              </>
            )}
          </div>
        </div>

        <div style={{ fontSize: 16, color: "rgba(255,255,255,0.25)", transition: "transform 0.3s", transform: open ? "rotate(180deg)" : "rotate(0deg)" }}>▼</div>
      </div>

      {open && (
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${game.accentColor}33` }}>
          <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 8 }}>
            {game.roadmapLabel}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {game.items.map(item => (
              <ItemRow key={item.id} item={item} now={now} color={game.accentColor} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ━━━ 메인 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export default function App() {
  const [now, setNow] = useState(new Date());
  const [open, setOpen] = useState(null);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", display: "flex", justifyContent: "center", alignItems: "flex-start", padding: "32px 16px 48px", fontFamily: "'Inter','Segoe UI',system-ui,sans-serif" }}>
      <div style={{ width: "100%", maxWidth: 440 }}>
        <div style={{ marginBottom: 28, textAlign: "center" }}>
          <div style={{ fontSize: 10, letterSpacing: 3, textTransform: "uppercase", color: "rgba(255,255,255,0.3)", marginBottom: 6, fontFamily: "monospace" }}>
            SEASON TRACKER
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#fff", letterSpacing: -0.5 }}>활성 시즌</div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", marginTop: 4 }}>
            {kfmt(now, { year: "numeric", month: "long", day: "numeric" })} 기준
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {GAMES.map(game => (
            <GameCard key={game.id} game={game} now={now}
              open={open === game.id}
              onToggle={() => setOpen(p => p === game.id ? null : game.id)}
            />
          ))}
        </div>

        <div style={{ textAlign: "center", marginTop: 28, fontSize: 10, color: "rgba(255,255,255,0.15)", letterSpacing: 0.5 }}>
          탭하면 로드맵 · 미발표 일정은 표시하지 않음
        </div>
      </div>
    </div>
  );
}
