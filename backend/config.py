import os
from typing import List
from dotenv import load_dotenv

# 환경에 따른 .env 파일 로드
env = os.getenv('ENV', 'dev')

if env == 'prod':
    load_dotenv('.env.prod')
elif env == 'dev':
    load_dotenv('.env.dev')

class Settings:
    """애플리케이션 설정 관리"""
    
    # 데이터베이스 설정 (.env에서 반드시 설정)
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')  # 개발용만 기본값
    DB_PORT: str = os.getenv('DB_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'octave')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'postgres')
    
    # API 서버 설정
    API_HOST: str = os.getenv('API_HOST') or '0.0.0.0'
    API_PORT: int = int(os.getenv('API_PORT') or '8000')
    API_RELOAD: bool = (os.getenv('API_RELOAD') or 'true').lower() == 'true'
    
    # CORS 설정
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    ALLOWED_ORIGINS: List[str] = [
        FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # 보안 설정
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'octave-super-secret-key-change-in-production')
    ALGORITHM: str = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    
    # 파일 업로드 설정
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    
    ALLOWED_AUDIO_FORMATS: List[str] = os.getenv(
        'ALLOWED_AUDIO_FORMATS', 
        'audio/mpeg,audio/wav,audio/mp4,audio/aac,audio/m4a,audio/webm'
    ).split(',')
    
    # 음성 분석 설정
    PITCH_THRESHOLD: float = float(os.getenv('PITCH_THRESHOLD', '0.1'))
    SAMPLE_RATE: int = int(os.getenv('SAMPLE_RATE', '22050'))
    CONFIDENCE_MIN_THRESHOLD: float = float(os.getenv('CONFIDENCE_MIN_THRESHOLD', '0.3'))
    
    FFMPEG_PATH: str = os.getenv('FFMPEG_PATH', 'ffmpeg')
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # 환경별 플래그
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    ENABLE_DOCS: bool = os.getenv('ENABLE_DOCS', 'true').lower() == 'true'
    ENV: str = os.getenv('ENV', 'dev')
    
    @property
    def database_url(self) -> str:
        """PostgreSQL 연결 URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# 전역 설정 인스턴스
settings = Settings()

# 개발/운영 환경 정보 출력
print(f"🚀 Octave API starting in {settings.ENV.upper()} mode")
if settings.DEBUG:
    print(f"📊 Debug mode: ON")
    print(f"📚 API Docs: {'ON' if settings.ENABLE_DOCS else 'OFF'}")
    print(f"🗄️  Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}") 