from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import librosa
import numpy as np
import io
from typing import List, Optional
from config import settings

app = FastAPI(title="Octave - 음역대 분석 API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

# Pydantic 모델들
class VocalRangeResult(BaseModel):
    lowest_note_hz: float
    highest_note_hz: float
    lowest_note_name: str
    highest_note_name: str
    vocal_range_type: str
    confidence_score: float

class SongRecommendation(BaseModel):
    id: int
    title: str
    artist: str
    genre: str
    compatibility_score: float
    key_adjustment: int
    original_key: str

class User(BaseModel):
    username: str
    email: str
    display_name: Optional[str] = None

# 주파수를 음표명으로 변환하는 함수
def hz_to_note(frequency):
    """주파수(Hz)를 음표명으로 변환"""
    if frequency <= 0:
        return "Unknown"
    
    # A4 = 440Hz를 기준으로 계산
    A4 = 440.0
    C0 = A4 * np.power(2, -4.75)  # C0 주파수
    
    if frequency > C0: # C0 이하는 인간이 발성하기 거의 불가능한 영역, 측정되더라도 노이즈나 하모닉스일 가능성이 높음
        h = round(12 * np.log2(frequency / C0))
        octave = h // 12
        n = h % 12
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return f"{note_names[n]}{octave}"
    return "Unknown"

def classify_vocal_range(lowest_hz, highest_hz):
    """음역대를 기반으로 성부 분류"""
    # 대략적인 성부 분류 (Hz 기준)
    ranges = {
        'bass': (82, 294),      # E2-D4
        'baritone': (98, 349),  # G2-F4
        'tenor': (131, 523),    # C3-C5
        'alto': (175, 698),     # F3-F5
        'mezzo-soprano': (220, 880),  # A3-A5
        'soprano': (262, 1047)  # C4-C6
    }
    
    best_match = 'unknown'
    best_overlap = 0
    
    for voice_type, (range_low, range_high) in ranges.items():
        # 겹치는 구간 계산
        overlap_low = max(lowest_hz, range_low)
        overlap_high = min(highest_hz, range_high)
        
        if overlap_high > overlap_low:
            overlap = overlap_high - overlap_low
            user_range = highest_hz - lowest_hz
            overlap_ratio = overlap / user_range if user_range > 0 else 0
            
            if overlap_ratio > best_overlap:
                best_overlap = overlap_ratio
                best_match = voice_type
    
    return best_match

def analyze_audio_pitch(audio_data, sr):
    """오디오에서 피치 분석하여 최고음/최저음 추출"""
    try:
        # 피치 추출 (환경변수 기반 임계값 사용)
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr, threshold=settings.PITCH_THRESHOLD)
        
        # 신뢰할 만한 피치만 추출
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:  # 유효한 피치만
                pitch_values.append(pitch)
        
        if not pitch_values:
            raise ValueError("유효한 피치를 찾을 수 없습니다")
        
        lowest_hz = min(pitch_values)
        highest_hz = max(pitch_values)
        
        # 신뢰도 계산 (검출된 피치의 비율)
        confidence = len(pitch_values) / pitches.shape[1]
        
        return lowest_hz, highest_hz, confidence
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"음성 분석 실패: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "🎵 Octave API가 실행 중입니다!", "version": "1.0.0"}

@app.post("/users", response_model=dict)
def create_user(user: User):
    """새 사용자 생성"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, email, display_name, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id, username, email, display_name, created_at
        """, (user.username, user.email, user.display_name, "temp_hash"))
        
        new_user = cur.fetchone()
        conn.commit()
        return dict(new_user)
        
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="사용자명 또는 이메일이 이미 존재합니다")
    finally:
        cur.close()
        conn.close()

@app.post("/analyze-vocal-range", response_model=VocalRangeResult)
async def analyze_vocal_range(
    audio_file: UploadFile = File(...),
    user_id: int = Form(...)
):
    """업로드된 오디오 파일에서 음역대 분석"""
    
    print("=== 받은 파일 정보 ===")
    print(f"파일명: {audio_file.filename}")
    print(f"Content-Type: {audio_file.content_type}")
    print(f"사이즈: {audio_file.size if hasattr(audio_file, 'size') else 'Unknown'} bytes")
    print(f"User ID: {user_id}")
    
    # 파일 내용 읽기 전 상태 확인
    print("=== 파일 읽기 시작 ===")
    
    if not audio_file.content_type:
        print("❌ Content-Type이 없습니다!")
        raise HTTPException(status_code=400, detail="파일의 Content-Type을 확인할 수 없습니다.")
    
    print(f"허용된 형식들: {settings.ALLOWED_AUDIO_FORMATS}")
    print(f"현재 파일 형식: {audio_file.content_type}")
    
    # Content-Type에서 기본 MIME 타입만 추출 (코덱 정보 제거)
    base_content_type = audio_file.content_type.split(';')[0].strip()
    print(f"기본 MIME 타입: {base_content_type}")
    print(f"형식 매치 여부: {base_content_type in settings.ALLOWED_AUDIO_FORMATS}")
    
    if base_content_type not in settings.ALLOWED_AUDIO_FORMATS:
        print(f"❌ 지원되지 않는 파일 형식: {base_content_type}")
        raise HTTPException(
            status_code=400, 
            detail=f"지원되지 않는 파일 형식입니다. 현재: {base_content_type}, 허용 형식: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
        )
    
    try:
        # 오디오 파일 읽기
        audio_bytes = await audio_file.read()
        print(f"=== 파일 읽기 완료 ===")
        print(f"실제 파일 크기: {len(audio_bytes)} bytes")
        print(f"파일 크기 (MB): {len(audio_bytes) / 1024 / 1024:.2f}")
        
        # 파일 헤더 확인 (처음 몇 바이트)
        header_bytes = audio_bytes[:16] if len(audio_bytes) > 16 else audio_bytes
        print(f"파일 헤더 (hex): {header_bytes.hex()}")
        
        if len(audio_bytes) == 0:
            print("❌ 파일이 비어있습니다!")
            raise HTTPException(status_code=400, detail="업로드된 파일이 비어있습니다.")
        
        if len(audio_bytes) < 1000:
            print("⚠️ 파일 크기가 매우 작습니다. 올바른 오디오 파일인지 확인이 필요합니다.")
        
        try:
            print("=== Librosa 로딩 시도 ===")
            # mp3, wav -> librosa로 로딩
            audio_data, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
            print(f"✅ Librosa 로딩 성공 - 샘플 레이트: {sr}, 데이터 길이: {len(audio_data)}")
        except Exception as load_error:
            print(f"❌ Librosa 로딩 실패: {load_error}")
            print("=== FFmpeg 변환 시도 ===")
            # webm, m4a, wav -> ffmpeg로 변환 후 로딩
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as temp_input:
                temp_input.write(audio_bytes)
                temp_input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            try:
                print(f"FFmpeg 명령어: {settings.FFMPEG_PATH} -i {temp_input_path} -ar 22050 -ac 1 {temp_output_path} -y")
                # FFmpeg로 wav 변환
                result = subprocess.run([
                    settings.FFMPEG_PATH, '-i', temp_input_path, 
                    '-ar', '22050', '-ac', '1', 
                    temp_output_path, '-y'
                ], check=True, capture_output=True, text=True)
                
                print(f"✅ FFmpeg 변환 성공")
                print(f"FFmpeg stdout: {result.stdout}")
                if result.stderr:
                    print(f"FFmpeg stderr: {result.stderr}")
                
                # 변환된 파일 로딩
                audio_data, sr = librosa.load(temp_output_path, sr=None)
                print(f"✅ 변환된 파일 로딩 성공 - 샘플 레이트: {sr}, 데이터 길이: {len(audio_data)}")
                
            except subprocess.CalledProcessError as ffmpeg_error:
                print(f"❌ FFmpeg 변환 실패: {ffmpeg_error}")
                print(f"FFmpeg stderr: {ffmpeg_error.stderr}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"오디오 파일 변환에 실패했습니다: {str(ffmpeg_error)}"
                )
            except Exception as ffmpeg_load_error:
                print(f"❌ 변환된 파일 로딩 실패: {ffmpeg_load_error}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"변환된 오디오 파일을 로드할 수 없습니다: {str(ffmpeg_load_error)}"
                )
            finally:
                # 임시 파일 정리
                import os
                try:
                    os.unlink(temp_input_path)
                    os.unlink(temp_output_path)
                except:
                    pass
        
        # 피치 분석
        lowest_hz, highest_hz, confidence = analyze_audio_pitch(audio_data, sr)
        
        # 음표명 변환
        lowest_note = hz_to_note(lowest_hz)
        highest_note = hz_to_note(highest_hz)
        
        # 성부 분류
        vocal_type = classify_vocal_range(lowest_hz, highest_hz)
        
        # 데이터베이스에 저장
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO vocal_range_sessions 
            (user_id, lowest_note_hz, highest_note_hz, lowest_note_name, 
             highest_note_name, vocal_range_type, confidence_score, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, float(lowest_hz), float(highest_hz), lowest_note, highest_note, 
              vocal_type, float(confidence), True))
        
        session_id = cur.fetchone()['id']
        conn.commit()
        
        cur.close()
        conn.close()
        
        return VocalRangeResult(
            lowest_note_hz=lowest_hz,
            highest_note_hz=highest_hz,
            lowest_note_name=lowest_note,
            highest_note_name=highest_note,
            vocal_range_type=vocal_type,
            confidence_score=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

@app.get("/users/{user_id}/song-recommendations", response_model=List[SongRecommendation])
def get_song_recommendations(user_id: int, limit: int = 10):
    """사용자의 최신 음역대를 기반으로 노래 추천"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 사용자의 최신 음역대 정보 가져오기
    cur.execute("""
        SELECT lowest_note_hz, highest_note_hz 
        FROM vocal_range_sessions 
        WHERE user_id = %s AND is_verified = TRUE
        ORDER BY session_date DESC 
        LIMIT 1
    """, (user_id,))
    
    user_range = cur.fetchone()
    if not user_range:
        raise HTTPException(status_code=404, detail="사용자의 음역대 정보를 찾을 수 없습니다")
    
    user_low, user_high = user_range['lowest_note_hz'], user_range['highest_note_hz']
    
    # 노래 추천 로직
    cur.execute("""
        SELECT id, title, artist, genre, original_key,
               lowest_note_hz, highest_note_hz
        FROM songs 
        WHERE is_active = TRUE
        ORDER BY 
            -- 음역대 겹침 정도로 정렬
            GREATEST(0, LEAST(%s, highest_note_hz) - GREATEST(%s, lowest_note_hz)) DESC
        LIMIT %s
    """, (user_high, user_low, limit))
    
    songs = cur.fetchall()
    recommendations = []
    
    for song in songs:
        # 적합도 점수 계산
        song_low, song_high = song['lowest_note_hz'], song['highest_note_hz']
        
        # 겹치는 음역대 계산
        overlap_low = max(user_low, song_low)
        overlap_high = min(user_high, song_high)
        overlap = max(0, overlap_high - overlap_low)
        
        song_range = song_high - song_low
        compatibility = overlap / song_range if song_range > 0 else 0
        
        # 키 조정 계산 (반음 단위, 1옥타브는 12반음)
        key_adjustment = 0
        if user_high < song_high:
            # 사용자가 높은 음을 못 내는 경우 키를 낮춤
            key_adjustment = -round(12 * np.log2(float(song_high) / float(user_high)))
        elif user_low > song_low:
            # 사용자가 낮은 음을 못 내는 경우 키를 높임
            key_adjustment = round(12 * np.log2(float(user_low) / float(song_low)))
        
        recommendations.append(SongRecommendation(
            id=song['id'],
            title=song['title'],
            artist=song['artist'],
            genre=song['genre'],
            compatibility_score=round(compatibility, 2),
            key_adjustment=key_adjustment,
            original_key=song['original_key']
        ))
    
    cur.close()
    conn.close()
    
    return recommendations

@app.get("/songs", response_model=List[dict])
def get_songs():
    """모든 노래 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, title, artist, album, genre, original_key,
               lowest_note_name, highest_note_name, difficulty_level
        FROM songs 
        WHERE is_active = TRUE
        ORDER BY title
    """)
    
    songs = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(song) for song in songs]

@app.get("/users/{user_id}/vocal-history")
def get_vocal_history(user_id: int):
    """사용자의 음역대 측정 기록"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT session_date, lowest_note_name, highest_note_name,
               vocal_range_type, confidence_score
        FROM vocal_range_sessions 
        WHERE user_id = %s AND is_verified = TRUE
        ORDER BY session_date DESC
    """, (user_id,))
    
    history = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(record) for record in history]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.API_RELOAD
    )
