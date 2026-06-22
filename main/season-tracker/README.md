# 🎮 Game Season Tracker — 실행 매뉴얼

## 📁 폴더 구조

```
season-tracker/
├── index.html
├── package.json
├── vite.config.js
├── README.md               ← 이 파일
└── src/
    ├── main.jsx
    ├── App.jsx             ← 메인 코드 (날짜·아이콘 수정은 여기)
    └── assets/
        └── logos/          ← 🖼️ 게임 로고 이미지를 여기에 넣으세요
            ├── d4.png
            ├── poe1.png
            ├── poe2.png
            ├── wow.png
            └── hs.png
```

---

## 🚀 처음 실행 (최초 1회)

터미널을 열고 아래 명령어를 순서대로 입력하세요.

```bash
# 1. Node.js 설치 여부 확인 (버전이 뜨면 설치된 것)
node -v

# 설치 안 돼 있다면 Homebrew로 설치:
brew install node

# 2. 이 폴더로 이동 (season-tracker 폴더 경로로 변경)
cd ~/Downloads/season-tracker

# 3. 패키지 설치 (최초 1회만)
npm install

# 4. 개발 서버 실행
npm run dev
```

터미널에 `http://localhost:5173` 이 뜨면 성공.  
브라우저에서 해당 주소를 열면 앱이 보입니다.

---

## 🔄 이후 실행 (매번)

```bash
cd ~/Downloads/season-tracker
npm run dev
```

종료할 때는 터미널에서 `Ctrl + C`

---

## 🖼️ 게임 로고 이미지 넣는 방법

### 1단계 — 이미지 파일 복사

로고 이미지(PNG 또는 WebP 권장, 정사각형)를 아래 폴더에 넣습니다:

```
season-tracker/src/assets/logos/
```

파일명 예시:
```
d4.png      → Diablo IV
poe1.png    → Path of Exile
poe2.png    → Path of Exile 2
wow.png     → World of Warcraft
hs.png      → Hearthstone
```

### 2단계 — App.jsx 상단에 import 추가

`src/App.jsx` 파일 맨 위 주석 블록을 찾아서 아래처럼 수정합니다:

```js
// 수정 전 (주석 처리된 상태)
// import d4Logo from "./assets/logos/d4.png";

// 수정 후 (주석 해제)
import d4Logo from "./assets/logos/d4.png";
import poe1Logo from "./assets/logos/poe1.png";
import poe2Logo from "./assets/logos/poe2.png";
import wowLogo  from "./assets/logos/wow.png";
import hsLogo   from "./assets/logos/hs.png";
```

### 3단계 — GAMES 배열에 logo 연결

`App.jsx`의 `GAMES` 배열에서 각 게임의 `logo: null` 줄을 찾아 교체합니다:

```js
// Diablo IV
logo: null,      →   logo: d4Logo,

// Path of Exile
logo: null,      →   logo: poe1Logo,

// Path of Exile 2
logo: null,      →   logo: poe2Logo,

// World of Warcraft
logo: null,      →   logo: wowLogo,

// Hearthstone
logo: null,      →   logo: hsLogo,
```

저장하면 브라우저가 자동으로 새로고침됩니다.

---

## ✏️ 날짜 수정 방법

`src/App.jsx`의 `GAMES` 배열에서 수정하면 됩니다.

```js
startDate: new Date("2026-04-28T00:00:00Z"),   // 시작일 (UTC 기준)
endDate:   new Date("2026-07-20T21:00:00Z"),   // 종료일 (null = 미발표)
endIsEstimate: true,   // true = "(추정)" 표시, false = 확정
```

날짜 형식: `"YYYY-MM-DDTHH:MM:SSZ"` (Z = UTC)  
종료일 미정이면: `endDate: null`

---

## 🎨 색상 변경 방법

각 게임의 `accentColor` 값을 수정합니다:

```js
accentColor: "#c0392b",   // 링·글씨 색상 (HEX)
glowColor: "rgba(192,57,43,0.35)",   // 카드 발광 색상
bgColor: "#1a0a0a",       // 카드 배경색
```

---

## 📦 빌드 (배포용 파일 생성)

```bash
npm run build
```

`dist/` 폴더에 정적 파일이 생성됩니다.  
이 폴더를 GitHub Pages, Vercel, Netlify 등에 올리면 됩니다.
