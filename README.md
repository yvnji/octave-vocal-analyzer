# 🎵 Octave - AI 음역대 분석 & 노래 추천 서비스

AI 기반 음성 분석으로 사용자의 음역대를 정확하게 측정하고 맞춤형 노래를 추천하는 웹 애플리케이션입니다.

## ✨ 주요 기능

- 🎤 **실시간 음성 녹음**: Web Audio API를 활용한 브라우저 기반 음성 녹음
- 🤖 **AI 음역대 분석**: librosa를 사용한 정밀한 음성 분석 및 음역대 측정
- 🎵 **맞춤 노래 추천**: 개인 음역대에 최적화된 노래 추천 및 키 조정 제안

## 🛠 기술 스택

### Frontend
- **React 18** + TypeScript
- **Tailwind CSS** - 모던한 UI 디자인
- **Web Audio API** - 브라우저 음성 녹음

### Backend  
- **FastAPI** - 고성능 Python 웹 프레임워크
- **librosa** - 음성 신호 처리 및 분석
- **PostgreSQL** - 관계형 데이터베이스
- **SQLAlchemy** - ORM

## 🚀 로컬 개발 환경 설정

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd Octave
```

### 2. 백엔드 설정
```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작
uvicorn main:app --reload
```

### 3. 프론트엔드 설정
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm start
```

## 🌐 배포 가이드

### 배포 방법: Vercel + Railway

#### 1. 백엔드 배포 (Railway)
```bash
# Railway CLI 설치
npm install -g @railway/cli

# 백엔드 디렉토리에서
cd backend
railway login
railway init
railway up

# 환경변수 설정
railway variables set DATABASE_URL="your-postgresql-url"
railway variables set FRONTEND_URL="https://your-app.vercel.app"
```

#### 2. 프론트엔드 배포 (Vercel)
```bash
# Vercel CLI 설치
npm install -g vercel

# 프론트엔드 디렉토리에서
cd frontend
vercel

# 환경변수 설정
vercel env add REACT_APP_API_URL
# 값: https://your-api.railway.app
```


## 📂 프로젝트 구조

```
Octave/
├── frontend/           # React 프론트엔드
│   ├── src/
│   │   ├── components/ # UI 컴포넌트
│   │   └── App.tsx     # 메인 앱 컴포넌트
│   └── package.json
├── backend/            # FastAPI 백엔드
│   ├── main.py         # API 엔드포인트
│   ├── audio_analysis.py # 음성 분석 로직
│   ├── database.py     # 데이터베이스 설정
│   └── requirements.txt
└── README.md
```

## 🔧 환경변수 설정

### 프론트엔드 (.env)
```env
REACT_APP_API_URL=http://localhost:8000
```

### 백엔드 (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/octave_db
FRONTEND_URL=http://localhost:3000
```

## 📊 데이터베이스 스키마

- **users**: 사용자 정보
- **songs**: 노래 데이터 (제목, 아티스트, 장르, 키 등)
- **user_vocal_ranges**: 사용자 음역대 측정 결과
- **song_recommendations**: 개인화된 노래 추천

---

Made with ❤️ for music lovers 