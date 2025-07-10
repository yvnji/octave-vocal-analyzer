import React, { useState, useEffect } from 'react';

interface VocalRangeResultProps {
  result: VocalRangeResult;
  userId: number;
}

interface VocalRangeResult {
  lowest_note_hz: number;
  highest_note_hz: number;
  lowest_note_name: string;
  highest_note_name: string;
  vocal_range_type: string;
  confidence_score: number;
}

interface SongRecommendation {
  id: number;
  title: string;
  artist: string;
  genre: string;
  compatibility_score: number;
  key_adjustment: number;
  original_key: string;
}

const VocalRangeResult: React.FC<VocalRangeResultProps> = ({ result, userId }) => {
  const [recommendations, setRecommendations] = useState<SongRecommendation[]>([]);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(true);

  useEffect(() => {
    fetchRecommendations();
  }, [userId]);

  const fetchRecommendations = async () => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/users/${userId}/song-recommendations`);
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  const getVocalTypeColor = (type: string) => {
    const colors = {
      'soprano': 'from-pink-400 to-rose-500',
      'mezzo-soprano': 'from-purple-400 to-pink-500',
      'alto': 'from-indigo-400 to-purple-500',
      'tenor': 'from-blue-400 to-indigo-500',
      'baritone': 'from-green-400 to-blue-500',
      'bass': 'from-gray-400 to-gray-600',
      'unknown': 'from-yellow-400 to-orange-500'
    };
    return colors[type as keyof typeof colors] || colors.unknown;
  };

  const getVocalTypeIcon = (type: string) => {
    const icons = {
      'soprano': '👩‍🎤',
      'mezzo-soprano': '🎭',
      'alto': '🎺',
      'tenor': '👨‍🎤',
      'baritone': '🎸',
      'bass': '🎻',
      'unknown': '🎵'
    };
    return icons[type as keyof typeof icons] || icons.unknown;
  };

  const getVocalTypeDescription = (type: string) => {
    const descriptions = {
      'soprano': '소프라노 - 가장 높은 여성 음역',
      'mezzo-soprano': '메조소프라노 - 중간 높이의 여성 음역',
      'alto': '알토 - 낮은 여성 음역',
      'tenor': '테너 - 높은 남성 음역',
      'baritone': '바리톤 - 중간 높이의 남성 음역',
      'bass': '베이스 - 가장 낮은 남성 음역',
      'unknown': '측정된 음역대'
    };
    return descriptions[type as keyof typeof descriptions] || descriptions.unknown;
  };

  const getKeyAdjustmentText = (adjustment: number, originalKey: string) => {
    if (adjustment === 0) return `${originalKey} (원곡 그대로)`;
    if (adjustment > 0) return `${originalKey} → ${adjustment}키 올림`;
    return `${originalKey} → ${Math.abs(adjustment)}키 내림`;
  };

  const getCompatibilityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCompatibilityIcon = (score: number) => {
    if (score >= 0.8) return '💚';
    if (score >= 0.6) return '💛';
    return '❤️';
  };

  return (
    <div className="space-y-6 w-full">
      {/* 헤더 */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-blue-500 shadow-lg mb-4">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M9 11H7v6h2v-6zm4 0h-2v6h2v-6zm4 0h-2v6h2v-6zm2.5-5H19V4h-3V2h-2v2H8V2H6v2H3v2h.5L5 8.5v12c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-12L20.5 6z"/>
          </svg>
        </div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent mb-2">
          🎵 음역대 분석 완료!
        </h2>
        <p className="text-gray-600 text-base">당신의 목소리를 분석한 결과입니다</p>
      </div>

      {/* 음역대 분석 결과 */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* 측정된 음역대 */}
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-100 via-purple-50 to-pink-100 rounded-2xl transform rotate-1 group-hover:rotate-2 transition-transform duration-300"></div>
          <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-white/50 hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center mb-4">
              <div className="p-2 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg mr-3">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 3l3.09 6.26L22 10.27l-5 4.87 1.18 6.88L12 18.77l-6.18 3.25L7 15.14 2 10.27l6.91-1.01L12 3z"/>
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-800">측정 결과</h3>
            </div>
            
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-xl p-4 border border-red-100">
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <span className="text-xl mr-2">🔻</span>
                    <span className="text-gray-600 font-medium text-sm">최저음</span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-red-600">{result.lowest_note_name}</div>
                    <div className="text-xs text-gray-500">{result.lowest_note_hz.toFixed(1)}Hz</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <span className="text-xl mr-2">🔺</span>
                    <span className="text-gray-600 font-medium text-sm">최고음</span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-600">{result.highest_note_name}</div>
                    <div className="text-xs text-gray-500">{result.highest_note_hz.toFixed(1)}Hz</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <span className="text-xl mr-2">📊</span>
                    <span className="text-gray-600 font-medium text-sm">정확도</span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-green-600">{(result.confidence_score * 100).toFixed(1)}%</div>
                    <div className="text-xs text-gray-500">신뢰도</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 성부 분류 */}
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-100 via-pink-50 to-orange-100 rounded-2xl transform -rotate-1 group-hover:-rotate-2 transition-transform duration-300"></div>
          <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-white/50 hover:shadow-2xl transition-all duration-300">
            <div className="text-center">
              <div className="mb-4">
                <div className="text-4xl mb-3">{getVocalTypeIcon(result.vocal_range_type)}</div>
                <div className={`inline-block px-4 py-2 rounded-full text-white font-bold text-base shadow-lg bg-gradient-to-r ${getVocalTypeColor(result.vocal_range_type)}`}>
                  {result.vocal_range_type.toUpperCase()}
                </div>
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-2">성부 분류</h3>
              <p className="text-gray-600 leading-relaxed text-sm">
                {getVocalTypeDescription(result.vocal_range_type)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 노래 추천 */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-br from-yellow-100/50 via-orange-50/50 to-red-100/50 rounded-2xl transform rotate-0.5"></div>
        <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-white/50">
          <div className="flex items-center justify-center mb-6">
            <div className="p-3 rounded-full bg-gradient-to-br from-orange-500 to-red-500 shadow-lg mr-3">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21s4.5-2.01 4.5-4.5V7h4V3h-7z"/>
              </svg>
            </div>
            <h3 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
              맞춤 노래 추천
            </h3>
          </div>
          
          {isLoadingRecommendations ? (
            <div className="flex flex-col items-center py-8">
              <div className="relative mb-4">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-orange-200 border-t-orange-500"></div>
                <div className="absolute inset-0 rounded-full border-4 border-red-200 border-t-red-500 animate-spin" style={{animationDirection: 'reverse', animationDuration: '2s'}}></div>
              </div>
              <span className="text-lg font-medium bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
                당신을 위한 완벽한 노래를 찾고 있어요...
              </span>
              <div className="mt-3 flex space-x-1">
                <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
                <div className="w-2 h-2 bg-red-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          ) : recommendations.length > 0 ? (
            <div className="grid gap-4 max-h-80 overflow-y-auto">
              {recommendations.map((song, index) => (
                <div key={song.id} className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-gray-100 to-blue-50 rounded-xl transform translate-x-1 translate-y-1 group-hover:translate-x-2 group-hover:translate-y-2 transition-transform duration-200"></div>
                  <div className="relative bg-white rounded-xl border-2 border-gray-100 p-4 hover:border-blue-200 transition-all duration-200 hover:shadow-lg">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center mb-1">
                          <span className="text-lg mr-2">🎵</span>
                          <h4 className="font-bold text-lg text-gray-800">{song.title}</h4>
                        </div>
                        <p className="text-gray-600 text-base mb-1">{song.artist}</p>
                        <span className="inline-block bg-gradient-to-r from-blue-500 to-purple-600 text-white text-xs px-2 py-1 rounded-full font-medium">
                          {song.genre}
                        </span>
                      </div>
                      <div className="text-right ml-3">
                        <div className="flex items-center mb-1">
                          <span className="text-lg mr-1">{getCompatibilityIcon(song.compatibility_score)}</span>
                          <div className={`text-base font-bold ${getCompatibilityColor(song.compatibility_score)}`}>
                            {(song.compatibility_score * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">적합도</div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg px-3 py-1 border border-indigo-100">
                        <span className="text-xs font-medium text-gray-700">
                          {getKeyAdjustmentText(song.key_adjustment, song.original_key)}
                        </span>
                      </div>
                      {song.key_adjustment !== 0 && (
                        <span className="bg-gradient-to-r from-orange-500 to-red-500 text-white text-xs px-2 py-1 rounded-full font-medium">
                          키 조정 추천
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-3">🎭</div>
              <p className="text-lg text-gray-600 mb-1">추천할 수 있는 노래를 찾지 못했습니다.</p>
              <p className="text-gray-500 text-sm">더 다양한 음역대로 다시 측정해보세요.</p>
            </div>
          )}
        </div>
      </div>

      {/* 다시 측정 버튼 */}
      <div className="text-center">
        <button
          onClick={() => window.location.reload()}
          className="group relative inline-flex items-center px-6 py-3 overflow-hidden text-base font-bold text-white rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 focus:ring-4 focus:ring-purple-300 transform transition-all duration-300 hover:scale-105 shadow-xl hover:shadow-2xl"
        >
          <span className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300"></span>
          <div className="flex items-center">
            <div className="mr-2 p-1 rounded-full bg-white/20 group-hover:bg-white/30 transition-colors duration-200">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
              </svg>
            </div>
            다시 측정하기
          </div>
        </button>
      </div>
    </div>
  );
};

export default VocalRangeResult; 