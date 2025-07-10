import React, { useState, useRef, useCallback } from 'react';
import type { VocalRangeResult } from '../types';

interface VoiceRecorderProps {
  onAnalysisComplete: (result: VocalRangeResult) => void;
  userId: number;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onAnalysisComplete, userId }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const uploadAndAnalyze = useCallback(async (audioBlob: Blob) => {
    setIsAnalyzing(true);
    
    try {
      console.log('Starting audio analysis...');
      console.log('Audio blob size:', audioBlob.size, 'bytes');
      console.log('Audio blob type:', audioBlob.type);

      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('user_id', userId.toString());

      // 환경변수 또는 기본값 사용
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const endpoint = `${apiUrl}/analyze-vocal-range`;
      
      console.log('Sending request to:', endpoint);

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        let errorMessage = '음성 분석에 실패했습니다.';
        
        try {
          const errorData = await response.json();
          console.error('Server error response:', errorData);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (jsonError) {
          console.error('Failed to parse error response as JSON:', jsonError);
          const errorText = await response.text();
          console.error('Error response text:', errorText);
          
          if (response.status === 404) {
            errorMessage = '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.';
          } else if (response.status === 500) {
            errorMessage = '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
          } else {
            errorMessage = `HTTP ${response.status}: ${errorText || '알 수 없는 오류가 발생했습니다.'}`;
          }
        }
        
        throw new Error(errorMessage);
      }

      const result: VocalRangeResult = await response.json();
      console.log('Analysis result:', result);
      onAnalysisComplete(result);
      
    } catch (err) {
      console.error('Analysis error details:', err);
      
      let userFriendlyMessage = '음성 분석 중 오류가 발생했습니다.';
      
      if (err instanceof TypeError && err.message.includes('fetch')) {
        userFriendlyMessage = '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.';
      } else if (err instanceof Error) {
        userFriendlyMessage = err.message;
      }
      
      setError(userFriendlyMessage);
    } finally {
      setIsAnalyzing(false);
    }
  }, [userId, onAnalysisComplete]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      
      // 브라우저 지원 오디오 형식 확인
      console.log('=== 브라우저 오디오 지원 정보 ===');
      console.log('MediaRecorder 지원 여부:', typeof MediaRecorder !== 'undefined');
      
      if (typeof MediaRecorder !== 'undefined') {
        const supportedTypes = [
          'audio/webm',
          'audio/webm;codecs=opus',
          'audio/webm;codecs=vorbis',
          'audio/mp4',
          'audio/mp4;codecs=mp4a.40.2',
          'audio/wav',
          'audio/ogg',
          'audio/ogg;codecs=opus'
        ];
        
        console.log('지원되는 오디오 형식:');
        supportedTypes.forEach(type => {
          console.log(`  ${type}: ${MediaRecorder.isTypeSupported(type)}`);
        });
      }
      
      // 마이크 권한 요청
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });

      // 최적의 MIME 타입 선택
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        const fallbackTypes = [
          'audio/webm',
          'audio/mp4',
          'audio/wav',
          'audio/ogg;codecs=opus'
        ];
        
        for (const type of fallbackTypes) {
          if (MediaRecorder.isTypeSupported(type)) {
            mimeType = type;
            break;
          }
        }
      }
      
      console.log('선택된 MIME 타입:', mimeType);

      // MediaRecorder 설정
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        console.log('=== 오디오 데이터 수신 ===');
        console.log('데이터 크기:', event.data.size, 'bytes');
        console.log('데이터 타입:', event.data.type);
        
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        console.log('=== 녹음 완료 ===');
        console.log('총 청크 수:', audioChunksRef.current.length);
        
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        
        console.log('=== 최종 오디오 파일 정보 ===');
        console.log('파일 크기:', audioBlob.size, 'bytes');
        console.log('파일 타입:', audioBlob.type);
        console.log('파일 크기 (MB):', (audioBlob.size / 1024 / 1024).toFixed(2));
        
        // 파일이 너무 작은지 확인
        if (audioBlob.size < 1000) {
          console.warn('⚠️ 파일 크기가 매우 작습니다. 녹음이 제대로 되지 않았을 수 있습니다.');
        }
        
        await uploadAndAnalyze(audioBlob);
        
        // 스트림 정리
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      
      // 타이머 시작
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error('Recording error:', err);
      setError('마이크 접근 권한이 필요합니다. 브라우저 설정을 확인해주세요.');
    }
  }, [uploadAndAnalyze]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [isRecording]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getRecordingInstructions = () => {
    if (recordingTime < 3) return "🎤 가장 낮은 소리를 내보세요...";
    if (recordingTime < 6) return "🎵 이제 가장 높은 소리를 내보세요...";
    return "✨ 다양한 높이의 소리를 내보세요...";
  };

  return (
    <div className="max-w-md mx-auto">
      {/* 메인 카드 */}
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
        {/* 헤더 */}
        <div className="text-center px-8 pt-8 pb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-lg">
            <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">음역대 측정</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            가장 낮은 소리부터 높은 소리까지<br/>
            자연스럽게 발성해 주세요
          </p>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="mx-8 mb-6">
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 녹음 상태 표시 */}
        {isRecording && (
          <div className="px-8 mb-6">
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-6 border border-blue-100">
              <div className="text-center">
                {/* 타이머 */}
                <div className="mb-4">
                  <div className="text-3xl font-mono font-bold text-blue-600 mb-2">
                    {formatTime(recordingTime)}
                  </div>
                  <div className="flex items-center justify-center space-x-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-gray-600 font-medium">녹음 중</span>
                  </div>
                </div>
                
                {/* 가이드 메시지 */}
                <div className="bg-white/60 rounded-xl p-3 border border-white/50">
                  <p className="text-sm font-medium text-gray-700">
                    {getRecordingInstructions()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 분석 중 상태 */}
        {isAnalyzing && (
          <div className="px-8 mb-6">
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl p-6 border border-purple-100">
              <div className="text-center">
                <div className="mb-4">
                  <div className="w-12 h-12 mx-auto relative">
                    <div className="absolute inset-0 rounded-full border-4 border-purple-200"></div>
                    <div className="absolute inset-0 rounded-full border-4 border-purple-600 border-t-transparent animate-spin"></div>
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-700 mb-2">
                  AI가 음성을 분석하고 있어요
                </p>
                <div className="flex justify-center space-x-1">
                  <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
                  <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 버튼 영역 */}
        <div className="px-8 pb-8">
          {!isRecording && !isAnalyzing && (
            <button
              onClick={startRecording}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-4 px-6 rounded-2xl transition-all duration-200 active:scale-95 shadow-lg hover:shadow-xl"
            >
              <div className="flex items-center justify-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
                </svg>
                녹음 시작
              </div>
            </button>
          )}

          {isRecording && (
            <button
              onClick={stopRecording}
              className="w-full bg-gray-600 hover:bg-gray-700 text-white font-semibold py-4 px-6 rounded-2xl transition-all duration-200 active:scale-95 shadow-lg"
            >
              <div className="flex items-center justify-center">
                <div className="w-4 h-4 bg-white rounded-sm mr-2"></div>
                녹음 완료
              </div>
            </button>
          )}
        </div>
      </div>

      {/* 가이드 정보 */}
      <div className="mt-6 bg-gray-50 rounded-2xl p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">녹음 가이드</h3>
        <div className="space-y-2">
          <div className="flex items-center text-sm text-gray-600">
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mr-3 flex-shrink-0"></div>
            <span>조용한 환경에서 녹음해주세요</span>
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <div className="w-1.5 h-1.5 bg-purple-400 rounded-full mr-3 flex-shrink-0"></div>
            <span>최소 5초 이상 다양한 높이로 발성</span>
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full mr-3 flex-shrink-0"></div>
            <span>마이크 권한 허용이 필요합니다</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceRecorder; 