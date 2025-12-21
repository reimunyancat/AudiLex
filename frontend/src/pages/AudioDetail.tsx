import { useEffect, useState, useRef, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client, { AudioDataResponse, AudioStatus } from "../api/client";
import { Layout } from "../components/Layout";
import { Button } from "../components/ui/Button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { ArrowLeft, Wand2, Languages, Mic } from "lucide-react";

export default function AudioDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [audioData, setAudioData] = useState<AudioDataResponse | null>(null);
  const [status, setStatus] = useState<AudioStatus | null>(null);
  const [progress, setProgress] = useState<{
    type: string;
    current: number;
    total: number;
  } | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeIndex, setActiveIndex] = useState(-1);
  const audioRef = useRef<HTMLVideoElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const subtitleRefs = useRef<(HTMLDivElement | null)[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchData();
    fetchStatus();

    const wsUrl = `ws://localhost:8000/ws/audio/${id}/`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log("WebSocket Connected");
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "audio_update") {
        const message = data.message;
        if (
          [
            "subtitle_complete",
            "translation_complete",
            "pronounce_complete",
          ].includes(message.type)
        ) {
          fetchData();
          fetchStatus();
          setProgress(null);
        } else if (
          [
            "subtitle_failed",
            "translation_failed",
            "pronounce_failed",
          ].includes(message.type)
        ) {
          fetchStatus();
          setProgress(null);
          alert(`Operation failed: ${message.data}`);
        } else if (
          ["translation_progress", "pronounce_progress"].includes(message.type)
        ) {
          setProgress({
            type:
              message.type === "translation_progress"
                ? "Translation"
                : "Pronunciation",
            current: message.data.index + 1,
            total: message.data.total,
          });

          setAudioData((prev) => {
            if (!prev) return null;
            // Check if prev.audio_data exists and has data property
            if (!prev.audio_data || !Array.isArray(prev.audio_data.data)) {
              return prev;
            }

            const newData = { ...prev };
            // Create a shallow copy of the data array to avoid mutating state directly
            const subtitles = [...newData.audio_data.data];

            if (subtitles[message.data.index]) {
              if (message.type === "translation_progress") {
                subtitles[message.data.index] = {
                  ...subtitles[message.data.index],
                  translate: message.data.text,
                };
              } else {
                subtitles[message.data.index] = {
                  ...subtitles[message.data.index],
                  pronounce: message.data.text,
                };
              }
            }
            // Update the nested structure correctly
            newData.audio_data = {
              ...newData.audio_data,
              data: subtitles,
            };
            return newData;
          });
        }
      }
    };

    wsRef.current.onclose = () => {
      console.log("WebSocket Disconnected");
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

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

  const triggerProcess = async (
    type: "subtitle" | "translation" | "pronounce"
  ) => {
    try {
      await client.get(`/make_${type}/${id}`);
      fetchStatus();
    } catch (e) {
      console.error(`Failed to trigger ${type}`, e);
      alert(`Failed to start ${type} generation.`);
    }
  };

  const timelines = useMemo(
    () => audioData?.audio_data?.data || [],
    [audioData]
  );

  useEffect(() => {
    const index = timelines.findIndex(
      (item) => currentTime >= item.start && currentTime < item.end
    );
    setActiveIndex(index);
  }, [currentTime, timelines]);

  useEffect(() => {
    if (activeIndex !== -1 && subtitleRefs.current[activeIndex]) {
      subtitleRefs.current[activeIndex]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [activeIndex]);

  if (!audioData || !status) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate("/")}>
            <ArrowLeft className="w-5 h-5 mr-2" />
            돌아가기
          </Button>
          <h1 className="text-2xl font-bold truncate flex-1">
            {status.youtube_title || "오디오 상세"}
          </h1>
          <div className="flex gap-2 items-center">
            <StatusBadge status={status.subtitle_status} label="자막" />
            <StatusBadge status={status.translation_status} label="번역" />
            <StatusBadge status={status.pronounce_status} label="발음" />
            {progress && (
              <Badge
                variant="default"
                className="animate-pulse border-indigo-500 text-indigo-400"
              >
                {progress.type}:{" "}
                {Math.round((progress.current / progress.total) * 100)}% (
                {progress.current}/{progress.total})
              </Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 왼쪽: 비디오 플레이어 & 컨트롤 */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="overflow-hidden bg-black">
              <video
                ref={audioRef}
                className="w-full aspect-video"
                controls
                onTimeUpdate={handleTimeUpdate}
                src={`data:${audioData.audio_file.content_type};base64,${audioData.audio_file.data}`}
              />
            </Card>

            <div className="grid grid-cols-3 gap-4">
              <Button
                size="lg"
                variant="secondary"
                className="h-auto py-6 flex flex-col gap-2"
                onClick={() => triggerProcess("subtitle")}
                disabled={
                  status.subtitle_status === "Processing" ||
                  status.subtitle_status === "Finished"
                }
              >
                <Mic className="w-6 h-6" />
                <span>자막 생성</span>
              </Button>
              <Button
                size="lg"
                variant="secondary"
                className="h-auto py-6 flex flex-col gap-2"
                onClick={() => triggerProcess("translation")}
                disabled={
                  status.translation_status === "Processing" ||
                  status.translation_status === "Finished" ||
                  status.subtitle_status !== "Finished"
                }
              >
                <Languages className="w-6 h-6" />
                <span>번역하기</span>
              </Button>
              <Button
                size="lg"
                variant="secondary"
                className="h-auto py-6 flex flex-col gap-2"
                onClick={() => triggerProcess("pronounce")}
                disabled={
                  status.pronounce_status === "Processing" ||
                  status.pronounce_status === "Finished" ||
                  status.subtitle_status !== "Finished"
                }
              >
                <Wand2 className="w-6 h-6" />
                <span>발음 분석 (한국어)</span>
              </Button>
            </div>
          </div>

          {/* 오른쪽: 자막 리스트 */}
          <div className="lg:col-span-1 h-[600px]">
            <Card className="h-full flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>자막</span>
                  <Badge variant="neutral">{timelines.length}개의 문장</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar"
              >
                {timelines.length === 0 ? (
                  <div className="text-center text-slate-500 py-12">
                    자막을 생성해주세요
                  </div>
                ) : (
                  timelines.map((item, idx) => (
                    <div
                      key={idx}
                      ref={(el) => (subtitleRefs.current[idx] = el)}
                      onClick={() => seekTo(item.start)}
                      className={`p-4 rounded-xl cursor-pointer transition-all duration-200 border ${
                        activeIndex === idx
                          ? "bg-indigo-500/10 border-indigo-500/50 shadow-lg shadow-indigo-500/10"
                          : "bg-slate-800/50 border-slate-700 hover:border-slate-600"
                      }`}
                    >
                      <div className="flex justify-between text-xs text-slate-500 mb-2">
                        <span>{item.start}s</span>
                        <span>#{item.index + 1}</span>
                      </div>
                      <p
                        className={`text-lg font-medium mb-2 ${
                          activeIndex === idx
                            ? "text-indigo-300"
                            : "text-slate-200"
                        }`}
                      >
                        {item.subtitle}
                      </p>
                      {item.pronounce && (
                        <p className="text-sm text-pink-400 mb-1 font-medium">
                          {item.pronounce}
                        </p>
                      )}
                      {item.translate && (
                        <p className="text-sm text-slate-400">
                          {item.translate}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
}

const StatusBadge = ({ status, label }: { status: string; label: string }) => {
  const statusMap: Record<string, string> = {
    Finished: "완료",
    Processing: "진행 중",
    Waiting: "대기 중",
    Failed: "실패",
  };

  const colorMap: Record<string, string> = {
    Finished: "bg-emerald-500 text-emerald-900",
    Processing: "bg-yellow-500 text-yellow-900",
    Waiting: "bg-slate-500 text-slate-900",
    Failed: "bg-red-500 text-red-900",
  };

  return (
    <div
      className={`flex items-center gap-1 text-xs font-medium rounded-full py-1 px-3 ${
        colorMap[status] || "bg-gray-500 text-gray-900"
      }`}
    >
      <div
        className={`w-2.5 h-2.5 rounded-full ${
          status === "Processing" ? "animate-pulse" : ""
        }`}
      />
      <span>{statusMap[status] || label}</span>
    </div>
  );
};
