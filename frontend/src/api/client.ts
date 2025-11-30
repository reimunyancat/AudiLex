import axios from 'axios';

const client = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AudioStatus {
  id: string;
  youtube_link: string;
  youtube_title: string;
  audio_dir: string;
  audio_status: 'Not Processed' | 'Processing' | 'Finished' | 'Failed';
  subtitle_status: 'Not Processed' | 'Processing' | 'Finished' | 'Failed';
  translation_status: 'Not Processed' | 'Processing' | 'Finished' | 'Failed';
  pronounce_status: 'Not Processed' | 'Processing' | 'Finished' | 'Failed';
}
  
export interface TimelineItem {
  index: number;
  start: number;
  end: number;
  subtitle: string;
  translate?: string;
  pronounce?: string;
}

export interface AudioDataResponse {
    audio_file: {
        name: string;
        content_type: string;
        data: string; // base64
    };
    audio_data: {
        data: TimelineItem[];
    };
}

export default client;
