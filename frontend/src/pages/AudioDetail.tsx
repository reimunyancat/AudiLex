import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client, { AudioDataResponse, AudioStatus } from '../api/client';
import { Layout } from '../components/Layout';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ArrowLeft, Wand2, Languages, Mic } from 'lucide-react';

export default function AudioDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [audioData, setAudioData] = useState<AudioDataResponse | null>(null);
  const [status, setStatus] = useState<AudioStatus | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeIndex, setActiveIndex] = useState(-1);
  const audioRef = useRef<HTMLAudioElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const subtitleRefs = useRef<(HTMLDivElement | null)[]>([]);

  // 초기 데이터랑 상태 가져오기
  useEffect(() => {
    if (!id) return;
    fetchData();
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // 과정이 끝났을 때 데이터 다시 가져오기
  useEffect(() => {
    if (status?.subtitle_status === 'Finished' || status?.translation_status === 'Finished' || status?.pronounce_status === 'Finished') {
      fetchData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.subtitle_status, status?.translation_status, status?.pronounce_status]);

  const fetchData = async () => {
    try {
      const res = await client.get(`/audio_data/${id}`);
      setAudioData(res.data);
    } catch (e) {
      console.error("Failed to fetch audio data", e);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await client.get(`/status/${id}`);
      setStatus(res.data);
    } catch (e) {
      console.error("Failed to fetch status", e);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const seekTo = (time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      audioRef.current.play();
    }
  };

  const triggerProcess = async (type: 'subtitle' | 'translation' | 'pronounce') => {
    try {
      await client.get(`/make_${type}/${id}`);
      fetchStatus();
    } catch (e) {
      console.error(`Failed to trigger ${type}`, e);
      alert(`Failed to start ${type} generation.`);
    }
  };

  const timelines = useMemo(() => audioData?.audio_data?.data || [], [audioData]);

  // 현재 재생 시간에 맞춰 활성화된 자막 인덱스 찾기
  useEffect(() => {
    const index = timelines.findIndex(
      (item) => currentTime >= item.start && currentTime < item.end
    );
    setActiveIndex(index);
  }, [currentTime, timelines]);

  // 활성화된 자막이 바뀌면 자동으로 스크롤 이동
  useEffect(() => {
    if (activeIndex !== -1 && subtitleRefs.current[activeIndex]) {
      subtitleRefs.current[activeIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [activeIndex]);

  if (!audioData || !status) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-[50vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      </Layout>
    );
  }

  const audioSrc = `data:${audioData.audio_file.content_type};base64,${audioData.audio_file.data}`;

  return (
    <Layout>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[calc(100vh-4rem)]">
        {/* 좌측 화면 : 오디오 플레이어 */}
        <div className="lg:col-span-1 space-y-6">
          <Button variant="link" onClick={() => navigate('/')} className="mb-4" size="np">
            <ArrowLeft className="w-4 h-4 mr-2" /> 홈으로 돌아가기
          </Button>

          <Card className="sticky top-4">
            <CardHeader>
              <CardTitle>{status.youtube_title || "오디오 콘텐츠"}</CardTitle>
              <p className="text-sm text-slate-500 mt-1 font-mono">{id}</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <audio
                ref={audioRef}
                controls
                src={audioSrc}
                onTimeUpdate={handleTimeUpdate}
                className="w-full"
              />
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider">작업</h4>
                <div className="grid gap-3">
                  <ProcessAction
                    icon={Wand2}
                    label="자막 생성"
                    status={status.subtitle_status}
                    onClick={() => triggerProcess('subtitle')}
                  />
                  <ProcessAction
                    icon={Languages}
                    label="번역"
                    status={status.translation_status}
                    onClick={() => triggerProcess('translation')}
                    disabled={status.subtitle_status !== 'Finished'}
                  />
                  <ProcessAction
                    icon={Mic}
                    label="발음 추가"
                    status={status.pronounce_status}
                    onClick={() => triggerProcess('pronounce')}
                    disabled={status.subtitle_status !== 'Finished'}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 우측 화면 : 자막 */}
        <div className="lg:col-span-2 flex flex-col h-[calc(100vh-4rem)] overflow-y-hidden">
          <div className="bg-gray-500/10 rounded-xl border border-slate-700 flex-1 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-700 bg-gray-500/10 backdrop-blur sticky top-0 z-10">
              <h3 className="font-semibold text-white">자막</h3>
            </div>

            <div
              ref={scrollContainerRef}
              className="overflow-y-auto p-4 space-y-3 flex-1"
            >
              {timelines.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4">
                  <Wand2 className="w-12 h-12 opacity-20" />
                  <p>자막이 없습니다. '자막 생성' 버튼을 눌러주세요.</p>
                </div>
              ) : (
                timelines.map((item, idx) => {
                  const isActive = currentTime >= item.start && currentTime < item.end;
                  if (!item.subtitle.trim()) return null;

                  return (
                    <div
                      key={idx}
                      ref={(el) => (subtitleRefs.current[idx] = el)}
                      onClick={() => seekTo(item.start)}
                      className={`p-4 rounded-lg cursor-pointer transition-all duration-200 border ${isActive
                        ? 'bg-black border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.1)]'
                        : 'bg-gray-500/10 border-transparent hover:bg-gray-500/20 hover:border-slate-600'
                        }`}
                    >
                      <div className="flex justify-between text-xs text-slate-500 mb-2 font-mono">
                        <span>{formatTime(item.start)}</span>
                        <span>{formatTime(item.end)}</span>
                      </div>

                      <p className={`text-lg mb-2 leading-relaxed ${isActive ? 'text-white font-medium' : 'text-slate-300'}`}>
                        {item.subtitle}
                      </p>

                      {(item.pronounce || item.translate) && (
                        <div className="space-y-1 mt-3 pt-3 border-t border-slate-700/50">
                          {item.pronounce && (
                            <p className="text-sm text-amber-400 font-mono">{item.pronounce}</p>
                          )}
                          {item.translate && (
                            <p className="text-sm text-emerald-400">{item.translate}</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

interface ProcessActionProps {
  icon: React.ElementType;
  label: string;
  status: string;
  onClick: () => void;
  disabled?: boolean;
}

const ProcessAction = ({ icon: Icon, label, status, onClick, disabled }: ProcessActionProps) => {
  const isProcessing = status === 'Processing';
  const isFinished = status === 'Finished';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-500/10 rounded-lg border border-slate-700">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-md ${isFinished ? 'bg-emerald-500/10 text-emerald-500' : 'bg-slate-700 text-slate-400'}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-sm font-medium text-slate-200">{label}</span>
      </div>

      {isFinished ? (
        <Badge variant="success">Completed</Badge>
      ) : isProcessing ? (
        <Badge variant="warning">Processing...</Badge>
      ) : (
        <Button
          size="sm"
          variant="secondary"
          onClick={onClick}
          disabled={disabled}
          className="text-xs"
        >
          Start
        </Button>
      )}
    </div>
  );
};
