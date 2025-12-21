import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import client, { AudioStatus } from "../api/client";
import { Trash, Youtube, ArrowRight, Clock, Upload } from "lucide-react";
import { Layout } from "../components/Layout";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card, CardContent } from "../components/ui/Card";
import { StatusBadge } from "../components/StatusBadge";

export default function Home() {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [statuses, setStatuses] = useState<AudioStatus[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStatuses();
  }, []);

  const fetchStatuses = async () => {
    try {
      const response = await client.get("/statuses/");
      setStatuses(response.data);
    } catch (error) {
      console.error("Failed to fetch statuses", error);
    }
  };

  const handleDownload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url && !file) return;
    setLoading(true);
    try {
      const formData = new FormData();
      if (file) {
        formData.append("file", file);
      } else {
        formData.append("video_url", url);
      }

      const response = await client.post("/download_audio/", formData);
      navigate(`/view/${response.data.audio_id}`);
    } catch (error) {
      console.error("Failed to download/upload audio", error);
      alert("작업을 시작하는데 실패했어요. 다시 시도해주세요.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUrl(""); // Clear URL if file is selected
    }
  };

  const handleDelete = async (id: string) => {
    const ok = window.confirm(
      "정말 이 오디오를 삭제하시겠어요? 이 작업은 되돌릴 수 없어요."
    );
    if (!ok) return;
    try {
      await client.delete(`/delete_audio/${id}`);
      fetchStatuses();
    } catch (error) {
      console.error("Failed to delete audio", error);
      alert("오디오를 삭제하는데 실패했어요.");
    }
  };

  return (
    <Layout>
      <div className="space-y-12">
        <section className="text-center space-y-6 py-4">
          <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
            AudiLex
          </h1>
          <div className="max-w-2xl mx-auto">
            <form onSubmit={handleDownload} className="flex flex-col gap-4">
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Youtube className="h-5 w-5 text-slate-500" />
                  </div>
                  <Input
                    type="text"
                    placeholder="유튜브 URL (예 : https://www.youtube.com/watch?v=qe6pI2nfkhc)"
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value);
                      setFile(null); // Clear file if URL is typed
                    }}
                    disabled={!!file}
                    className="pl-10 py-3 text-lg"
                  />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="h-px flex-1 bg-slate-800"></div>
                <span className="text-slate-500 text-sm">또는</span>
                <div className="h-px flex-1 bg-slate-800"></div>
              </div>

              <div className="flex gap-3">
                <div className="relative flex-1">
                  <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept="video/*,audio/*"
                    onChange={handleFileChange}
                  />
                  <label
                    htmlFor="file-upload"
                    className={`flex items-center justify-center w-full px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                      file
                        ? "border-indigo-500 bg-indigo-500/10 text-indigo-400"
                        : "border-slate-700 hover:border-slate-500 text-slate-500"
                    }`}
                  >
                    <Upload className="w-5 h-5 mr-2" />
                    {file ? file.name : "파일 업로드 (영상 또는 오디오)"}
                  </label>
                </div>
                <Button
                  type="submit"
                  size="lg"
                  isLoading={loading}
                  className="shrink-0"
                >
                  생성하기 <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </div>
            </form>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <Clock className="w-6 h-6 text-indigo-400" />
              모든 오디오
            </h2>
          </div>
          <div className="grid gap-4">
            {statuses.length === 0 ? (
              <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-slate-800 border-dashed">
                <p className="text-slate-500">아직 변환된 오디오가 없습니다.</p>
              </div>
            ) : (
              statuses.map((item) => (
                <Card
                  key={item.id}
                  onClick={() => navigate(`/view/${item.id}`)}
                  className="group hover:border-indigo-500/50 transition-all duration-300"
                >
                  <CardContent className="flex items-center justify-between p-6">
                    <div className="flex-1 min-w-0 mr-6">
                      <h3 className="text-lg font-semibold text-white truncate group-hover:text-indigo-400 transition-colors">
                        {item.youtube_title || item.youtube_link}
                      </h3>
                      <p className="text-sm text-slate-500 font-mono mt-1">
                        {item.id}
                      </p>

                      <div className="flex flex-wrap gap-4 mt-3">
                        <StatusBadge
                          label="오디오"
                          status={item.audio_status}
                        />
                        <StatusBadge
                          label="자막"
                          status={item.subtitle_status}
                        />
                        <StatusBadge
                          label="번역"
                          status={item.translation_status}
                        />
                        <StatusBadge
                          label="발음"
                          status={item.pronounce_status}
                        />
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(item.id);
                      }}
                      className="text-slate-500 hover:text-red-400 hover:bg-red-400/10"
                    >
                      <Trash className="w-5 h-5" />
                    </Button>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </section>
      </div>
    </Layout>
  );
}
