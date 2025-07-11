import os
from typing import List
from dotenv import load_dotenv
import urllib.parse

# 환경에 따른 .env 파일 로드
env = os.getenv('ENV', 'dev')

if env == 'prod':
    load_dotenv('.env.prod')
elif env == 'dev':
    load_dotenv('.env.dev')

class Settings:
    """애플리케이션 설정 관리"""
    
    def __init__(self):
        # 데이터베이스 설정 - DATABASE_URL 우선 사용 (Render용)
        self._database_url = os.getenv('DATABASE_URL')
        
        if self._database_url:
            # DATABASE_URL이 있으면 파싱해서 사용
            parsed = urllib.parse.urlparse(self._database_url)
            self.DB_HOST = parsed.hostname or 'localhost'
            self.DB_PORT = str(parsed.port or 5432)
            self.DB_NAME = parsed.path.lstrip('/') or 'octave'
            self.DB_USER = parsed.username or 'postgres'
            self.DB_PASSWORD = parsed.password or 'postgres'
        else:
            # DATABASE_URL이 없으면 개별 환경변수 사용
            self.DB_HOST = os.getenv('DB_HOST', 'localhost')
            self.DB_PORT = os.getenv('DB_PORT', '5432')
            self.DB_NAME = os.getenv('DB_NAME', 'octave')
            self.DB_USER = os.getenv('DB_USER', 'postgres')
            self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
        
        # API 서버 설정 - Render.com의 PORT 환경변수 우선 사용
        self.API_HOST = os.getenv('API_HOST') or '0.0.0.0'
        self.API_PORT = int(os.getenv('PORT') or os.getenv('API_PORT') or '8000')
        self.API_RELOAD = (os.getenv('API_RELOAD') or 'true').lower() == 'true'
        
        # CORS 설정
        self.FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.ALLOWED_ORIGINS = [
            self.FRONTEND_URL,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://octave-ai.netlify.app",  # Netlify 프론트엔드
            "https://*.netlify.app"  # 모든 Netlify 도메인
        ]
        
        # 보안 설정
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'octave-super-secret-key-change-in-production')
        self.ALGORITHM = os.getenv('ALGORITHM', 'HS256')
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        
        # 파일 업로드 설정
        self.MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
        self.MAX_FILE_SIZE_BYTES = self.MAX_FILE_SIZE_MB * 1024 * 1024
        
        self.ALLOWED_AUDIO_FORMATS = os.getenv(
            'ALLOWED_AUDIO_FORMATS', 
            'audio/mpeg,audio/wav,audio/mp4,audio/aac,audio/m4a,audio/webm'
        ).split(',')
        
        # 음성 분석 설정
        self.PITCH_THRESHOLD = float(os.getenv('PITCH_THRESHOLD', '0.1'))
        self.SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', '22050'))
        self.CONFIDENCE_MIN_THRESHOLD = float(os.getenv('CONFIDENCE_MIN_THRESHOLD', '0.3'))
        
        self.FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
        
        # 로깅 설정
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # 환경별 플래그
        self.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
        self.ENABLE_DOCS = os.getenv('ENABLE_DOCS', 'true').lower() == 'true'
        self.ENV = os.getenv('ENV', 'dev')
    
    @property
    def database_url(self) -> str:
        """PostgreSQL 연결 URL"""
        return self._database_url or f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# 전역 설정 인스턴스
settings = Settings()

# 개발/운영 환경 정보 출력
print(f"🚀 Octave API starting in {settings.ENV.upper()} mode")
if settings.DEBUG:
    print(f"📊 Debug mode: ON")
    print(f"📚 API Docs: {'ON' if settings.ENABLE_DOCS else 'OFF'}")
    print(f"🗄️  Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
print(f"🌐 Server will run on port: {settings.API_PORT}") 