import React, { useState } from 'react';
import './App.css';
import VoiceRecorder from './components/VoiceRecorder';
import VocalRangeResultComponent from './components/VocalRangeResult';

interface VocalRangeAnalysisResult {
  lowest_note_hz: number;
  highest_note_hz: number;
  lowest_note_name: string;
  highest_note_name: string;
  vocal_range_type: string;
  confidence_score: number;
}

function App() {
  const [currentUserId] = useState(1); // 임시 사용자 ID (추후 로그인 시스템으로 대체)
  const [vocalRangeResult, setVocalRangeResult] = useState<VocalRangeAnalysisResult | null>(null);

  const handleAnalysisComplete = (result: VocalRangeAnalysisResult) => {
    setVocalRangeResult(result);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 네비게이션 바 */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-sm font-bold">O</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Octave</span>
            </div>
            
            {vocalRangeResult && (
              <button
                onClick={() => setVocalRangeResult(null)}
                className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
              >
                새로 측정
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!vocalRangeResult ? (
          <div className="max-w-4xl mx-auto">
            {/* 히어로 섹션 */}
            <div className="text-center mb-12">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
                당신의 음역대를
                <br />
                <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  정확하게 측정
                </span>
                하세요
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
                AI 기반 음성 분석으로 당신에게 완벽한 노래를 추천받아보세요
              </p>
              
              {/* 특징 카드들 */}
              <div className="grid md:grid-cols-3 gap-6 mb-12">
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4 mx-auto">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">정확한 분석</h3>
                  <p className="text-sm text-gray-600">AI가 당신의 음역대를 정밀하게 측정합니다</p>
                </div>
                
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4 mx-auto">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">맞춤 추천</h3>
                  <p className="text-sm text-gray-600">당신의 음역대에 최적화된 노래를 추천</p>
                </div>
                
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4 mx-auto">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">실시간 분석</h3>
                  <p className="text-sm text-gray-600">즉시 결과를 확인하고 키 조정 제안</p>
                </div>
              </div>
            </div>

            {/* 음성 녹음 섹션 */}
            <div className="bg-white rounded-3xl shadow-lg border border-gray-200 overflow-hidden">
              <div className="p-8">
                <VoiceRecorder 
                  onAnalysisComplete={handleAnalysisComplete}
                  userId={currentUserId}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-3xl shadow-lg border border-gray-200 overflow-hidden">
            <div className="p-8">
              <VocalRangeResultComponent 
                result={vocalRangeResult}
                userId={currentUserId}
              />
            </div>
          </div>
        )}
      </main>

      {/* 푸터 */}
      <footer className="border-t border-gray-200 bg-white mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xs font-bold">O</span>
              </div>
              <span className="font-semibold text-gray-900">Octave</span>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              AI 음성 분석 기반 노래 추천 서비스
            </p>
            <div className="flex justify-center space-x-6 text-xs text-gray-500">
              <span>정확한 측정</span>
              <span>•</span>
              <span>개인화 추천</span>
              <span>•</span>
              <span>실시간 분석</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
