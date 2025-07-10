export interface VocalRangeResult {
  lowest_note_hz: number;
  highest_note_hz: number;
  lowest_note_name: string;
  highest_note_name: string;
  vocal_range_type: string;
  confidence_score: number;
}

export interface SongRecommendation {
  id: number;
  title: string;
  artist: string;
  genre: string;
  compatibility_score: number;
  key_adjustment: number;
  original_key: string;
} 