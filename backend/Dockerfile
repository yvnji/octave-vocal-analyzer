FROM python:3.9-slim

# 시스템 패키지 설치 (librosa와 오디오 처리를 위해 필요)
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 설정
EXPOSE 8000

# 애플리케이션 시작
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 