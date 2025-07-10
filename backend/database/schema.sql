-- Octave 음역대 분석 서비스 데이터베이스 스키마
-- PostgreSQL 데이터베이스 생성
CREATE DATABASE octave;

-- 사용자 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    profile_image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 음역대 측정 세션 테이블
CREATE TABLE vocal_range_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    lowest_note_hz DECIMAL(8,2) NOT NULL,  -- 가장 낮은 음의 주파수 (Hz)
    highest_note_hz DECIMAL(8,2) NOT NULL, -- 가장 높은 음의 주파수 (Hz)
    lowest_note_name VARCHAR(10),          -- 음표명 (예: C2, D#3)
    highest_note_name VARCHAR(10),         -- 음표명 (예: A4, F#5)
    vocal_range_type VARCHAR(20),          -- 성부 분류 (soprano, alto, tenor, bass 등)
    confidence_score DECIMAL(3,2),         -- 측정 신뢰도 (0.0 ~ 1.0)
    audio_file_path TEXT,                  -- 원본 오디오 파일 경로 (선택적)
    analysis_metadata JSONB,               -- 상세 분석 데이터 (주파수 분포, 배음 등)
    is_verified BOOLEAN DEFAULT FALSE      -- 검증된 측정인지 여부
);

-- 노래 테이블
CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(100) NOT NULL,
    album VARCHAR(200),
    genre VARCHAR(50),
    release_year INTEGER,
    duration_seconds INTEGER,
    original_key VARCHAR(10),              -- 원곡 조성 (예: C, D#, Bb)
    lowest_note_hz DECIMAL(8,2),          -- 노래의 최저음
    highest_note_hz DECIMAL(8,2),         -- 노래의 최고음
    lowest_note_name VARCHAR(10),
    highest_note_name VARCHAR(10),
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    youtube_url TEXT,
    spotify_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 사용자-노래 추천 매핑 테이블
CREATE TABLE user_song_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    vocal_range_session_id INTEGER REFERENCES vocal_range_sessions(id) ON DELETE CASCADE,
    compatibility_score DECIMAL(3,2),     -- 적합도 점수 (0.0 ~ 1.0)
    key_adjustment INTEGER DEFAULT 0,      -- 키 조정 (반음 단위, -12 ~ +12)
    recommended_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    UNIQUE(user_id, song_id, vocal_range_session_id)
);

-- 친구 관계 테이블 (소셜 기능용)
CREATE TABLE user_friendships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    friend_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'blocked')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, friend_id),
    CHECK (user_id != friend_id)
);

-- 음역대 비교 기록 테이블
CREATE TABLE vocal_range_comparisons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    target_song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    user_vocal_session_id INTEGER REFERENCES vocal_range_sessions(id) ON DELETE CASCADE,
    required_key_adjustment INTEGER,       -- 필요한 키 조정
    difficulty_assessment VARCHAR(20),     -- 'easy', 'moderate', 'hard', 'impossible'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_vocal_sessions_user_date ON vocal_range_sessions(user_id, session_date DESC);
CREATE INDEX idx_songs_artist_title ON songs(artist, title);
CREATE INDEX idx_songs_genre ON songs(genre);
CREATE INDEX idx_songs_vocal_range ON songs(lowest_note_hz, highest_note_hz);
CREATE INDEX idx_recommendations_user_score ON user_song_recommendations(user_id, compatibility_score DESC);
CREATE INDEX idx_friendships_user_status ON user_friendships(user_id, status);

-- 트리거 함수: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 적용
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_songs_updated_at BEFORE UPDATE ON songs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 샘플 데이터 삽입
INSERT INTO users (username, email, password_hash, display_name) VALUES
('testuser1', 'test1@example.com', '$2b$12$hashedpassword1', '테스트유저1'),
('testuser2', 'test2@example.com', '$2b$12$hashedpassword2', '테스트유저2');

INSERT INTO songs (title, artist, album, genre, original_key, lowest_note_hz, highest_note_hz, 
                   lowest_note_name, highest_note_name, difficulty_level) VALUES
('Spring Day', 'BTS', 'You Never Walk Alone', 'K-Pop', 'F', 174.61, 659.25, 'F3', 'E5', 3),
('IU - Through the Night', 'IU', 'Palette', 'K-Pop', 'G', 196.00, 783.99, 'G3', 'G5', 2),
('Ed Sheeran - Perfect', 'Ed Sheeran', '÷', 'Pop', 'G', 146.83, 587.33, 'D3', 'D5', 2),
('Adele - Someone Like You', 'Adele', '21', 'Pop', 'A', 220.00, 880.00, 'A3', 'A5', 4);

-- 뷰 생성: 사용자별 최신 음역대 정보
CREATE VIEW user_latest_vocal_range AS
SELECT DISTINCT ON (user_id)
    user_id,
    lowest_note_hz,
    highest_note_hz,
    lowest_note_name,
    highest_note_name,
    vocal_range_type,
    session_date
FROM vocal_range_sessions
WHERE is_verified = TRUE
ORDER BY user_id, session_date DESC;

-- 뷰 생성: 노래별 추천 통계
CREATE VIEW song_recommendation_stats AS
SELECT 
    s.id,
    s.title,
    s.artist,
    COUNT(usr.id) as total_recommendations,
    AVG(usr.compatibility_score) as avg_compatibility,
    AVG(usr.user_rating) as avg_user_rating
FROM songs s
LEFT JOIN user_song_recommendations usr ON s.id = usr.song_id
GROUP BY s.id, s.title, s.artist; 