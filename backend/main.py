from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import librosa
import numpy as np
import io
import os
import signal
import subprocess
import tempfile
import warnings
from typing import List, Optional, Dict, Any, cast
from config import settings

# Librosa 초기화 (JIT 컴파일 문제 해결)
try:
    warnings.filterwarnings('ignore', category=UserWarning, module='numba')
    warnings.filterwarnings('ignore', category=FutureWarning, module='librosa')
    
    # librosa JIT 컴파일 문제 해결을 위한 더미 호출
    dummy_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 22050))
    _ = librosa.piptrack(y=dummy_audio, sr=22050, threshold=0.1)
    print("✅ Librosa initialized")
except Exception as e:
    print(f"⚠️ Librosa init warning: {e}")

app = FastAPI(title="Octave - 음역대 분석 API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "dev" else settings.ALLOWED_ORIGINS,
    allow_credentials=False if settings.ENV == "dev" else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 타임아웃 핸들러
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Processing timeout")

def init_database():
    """데이터베이스 테이블 초기화"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # CREATE DATABASE 명령어 제거
        schema_lines = schema_sql.split('\n')
        filtered_lines = [line for line in schema_lines if not line.strip().startswith('CREATE DATABASE')]
        schema_sql = '\n'.join(filtered_lines)
        
        cur.execute(schema_sql)
        conn.commit()
        print("✅ Database initialized")
        
    except psycopg2.errors.DuplicateTable:
        print("ℹ️ Database tables already exist")
    except FileNotFoundError:
        print("⚠️ Schema file not found")
    except Exception as e:
        print(f"❌ Database init failed: {e}")
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Octave API...")
    init_database()

def get_db_connection():
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=10
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

def load_audio_file(audio_path_or_bytes, sr=22050):
    """오디오 파일 로딩 (librosa 또는 FFmpeg 사용)"""
    try:
        # 직접 librosa로 로딩 시도
        if isinstance(audio_path_or_bytes, (str, os.PathLike)):
            audio_data, actual_sr = librosa.load(audio_path_or_bytes, sr=sr)
        else:
            audio_data, actual_sr = librosa.load(audio_path_or_bytes, sr=sr)
        return audio_data, actual_sr
    except Exception:
        # 바이트 스트림은 FFmpeg 변환 필요
        raise HTTPException(
            status_code=400, 
            detail="오디오 파일을 로드할 수 없습니다. FFmpeg 변환이 필요합니다."
        )

def analyze_audio_pitch(audio_data, sr):
    """오디오에서 피치 분석하여 최고음/최저음 추출"""
    try:
        # 오디오 길이 제한 (최대 60초)
        max_samples = int(60.0 * sr)
        if len(audio_data) > max_samples:
            audio_data = audio_data[:max_samples]
        
        # 무음 구간 제거
        try:
            non_silent_intervals = librosa.effects.split(audio_data, top_db=20)
            if len(non_silent_intervals) == 0:
                raise ValueError("오디오에서 음성을 찾을 수 없습니다.")
        except Exception:
            pass  # 무음 제거 실패시 무시하고 계속
        
        # 피치 추출
        pitches, magnitudes = librosa.piptrack(
            y=audio_data, 
            sr=sr, 
            threshold=max(settings.PITCH_THRESHOLD, 0.2),
            hop_length=512,
            fmin=80.0,
            fmax=2000.0
        )
        
        # 유효한 피치만 추출
        pitch_values = []
        time_step = max(1, pitches.shape[1] // 1000)
        
        for t in range(0, pitches.shape[1], time_step):
            if t >= pitches.shape[1]:
                break
                
            magnitude_column = magnitudes[:, t]
            if magnitude_column.max() > 0:
                index = magnitude_column.argmax()
                pitch = pitches[index, t]
                
                if 80.0 <= pitch <= 2000.0:
                    pitch_values.append(pitch)
        
        if len(pitch_values) < 10:
            raise ValueError("충분한 음성 데이터를 찾을 수 없습니다.")
        
        # 극값 제거 (상위/하위 5%)
        pitch_values = sorted(pitch_values)
        trim_count = max(1, len(pitch_values) // 20)
        if len(pitch_values) > trim_count * 2:
            pitch_values = pitch_values[trim_count:-trim_count]
        
        lowest_hz = min(pitch_values)
        highest_hz = max(pitch_values)
        confidence = min(1.0, len(pitch_values) / (pitches.shape[1] / time_step))
        
        return lowest_hz, highest_hz, confidence
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"음성 분석 실패: {str(e)}")

@app.get("/")
@app.head("/")
def read_root():
    return {"message": "🎵 Octave API가 실행 중입니다!", "version": "1.0.0", "status": "healthy"}

@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "healthy", "service": "octave-api"}

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
        if new_user is None:
            raise HTTPException(status_code=500, detail="사용자 생성에 실패했습니다")
        
        conn.commit()
        return dict(new_user)
        
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="사용자명 또는 이메일이 이미 존재합니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 생성 실패: {str(e)}")
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@app.post("/analyze-vocal-range", response_model=VocalRangeResult)
async def analyze_vocal_range(
    audio_file: UploadFile = File(...),
    user_id: int = Form(...)
):
    """업로드된 오디오 파일에서 음역대 분석"""
    
    if not audio_file.content_type:
        raise HTTPException(status_code=400, detail="파일의 Content-Type을 확인할 수 없습니다.")
    
    # Content-Type 체크
    base_content_type = audio_file.content_type.split(';')[0].strip()
    if base_content_type not in settings.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"지원되지 않는 파일 형식입니다. 허용 형식: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
        )
    
    try:
        # 파일 읽기
        audio_bytes = await audio_file.read()
        
        # 파일 크기 체크
        if len(audio_bytes) > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413, 
                detail=f"파일 크기가 너무 큽니다. 최대 {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="업로드된 파일이 비어있습니다.")
        
        # 타임아웃 설정 (60초)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)
        
        try:
            # 오디오 로딩 시도
            audio_data, sr = load_audio_file(io.BytesIO(audio_bytes), sr=22050)
            
            # 오디오 길이 체크
            duration = len(audio_data) / sr
            if duration < 1.0:
                raise HTTPException(status_code=400, detail="오디오가 너무 짧습니다. 최소 1초 이상 필요합니다.")
                
        except HTTPException:
            # FFmpeg 변환 시도
            temp_input_path = None
            temp_output_path = None
            
            try:
                with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as temp_input:
                    temp_input.write(audio_bytes)
                    temp_input_path = temp_input.name
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                    temp_output_path = temp_output.name
                
                # FFmpeg 변환
                subprocess.run([
                    settings.FFMPEG_PATH, '-i', temp_input_path, 
                    '-ar', '22050', '-ac', '1', '-t', '120',
                    temp_output_path, '-y'
                ], check=True, capture_output=True, text=True, timeout=30)
                
                # 변환된 파일 로딩
                audio_data, sr = load_audio_file(temp_output_path, sr=22050)
                
                duration = len(audio_data) / sr
                if duration < 1.0:
                    raise HTTPException(status_code=400, detail="변환된 오디오가 너무 짧습니다.")
                
            except subprocess.TimeoutExpired:
                raise HTTPException(status_code=408, detail="오디오 파일 변환 시간 초과")
            except subprocess.CalledProcessError as e:
                raise HTTPException(status_code=400, detail="오디오 파일 변환 실패")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"오디오 처리 실패: {str(e)}")
            finally:
                # 임시 파일 정리
                for path in [temp_input_path, temp_output_path]:
                    if path and os.path.exists(path):
                        try:
                            os.unlink(path)
                        except:
                            pass
        
        # 피치 분석
        signal.alarm(30)  # 피치 분석 타임아웃
        try:
            lowest_hz, highest_hz, confidence = analyze_audio_pitch(audio_data, sr)
        finally:
            signal.alarm(0)
        
        # 음표명 변환
        lowest_note = hz_to_note(lowest_hz)
        highest_note = hz_to_note(highest_hz)
        vocal_type = classify_vocal_range(lowest_hz, highest_hz)
        
        # 데이터베이스에 저장
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO vocal_range_sessions 
                (user_id, lowest_note_hz, highest_note_hz, lowest_note_name, 
                 highest_note_name, vocal_range_type, confidence_score, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, float(lowest_hz), float(highest_hz), lowest_note, highest_note, 
                  vocal_type, float(confidence), True))
            
            result = cur.fetchone()
            if result is None:
                raise HTTPException(status_code=500, detail="데이터 저장 실패")
            
            result_dict = cast(Dict[str, Any], result)
            session_id = result_dict['id']
            conn.commit()
            
        except Exception as db_error:
            raise HTTPException(status_code=500, detail=f"데이터베이스 오류: {str(db_error)}")
        finally:
            try:
                cur.close()
                conn.close()
            except:
                pass
        
        return VocalRangeResult(
            lowest_note_hz=lowest_hz,
            highest_note_hz=highest_hz,
            lowest_note_name=lowest_note,
            highest_note_name=highest_note,
            vocal_range_type=vocal_type,
            confidence_score=confidence
        )
        
    except TimeoutError:
        raise HTTPException(status_code=408, detail="처리 시간 초과")
    except HTTPException:
        raise  # HTTPException은 그대로 전달
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")
    finally:
        signal.alarm(0)

@app.get("/users/{user_id}/song-recommendations", response_model=List[SongRecommendation])
def get_song_recommendations(user_id: int, limit: int = 10):
    """사용자의 최신 음역대를 기반으로 노래 추천"""
    
    conn = get_db_connection()
    try:
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
        if user_range is None:
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
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 조회 실패: {str(e)}")
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

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
    print(f"🚀 Starting Octave API on {settings.API_HOST}:{settings.API_PORT}")
    print(f"🔧 Environment: {settings.ENV}")
    print(f"🔧 Reload mode: {settings.API_RELOAD}")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.API_RELOAD,
        log_level="info"
    )
