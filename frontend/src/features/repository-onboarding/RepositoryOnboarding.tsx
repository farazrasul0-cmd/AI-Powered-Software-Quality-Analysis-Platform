import React, { useState } from "react";
import { CheckCircle2, GitBranch, Github, Loader2, Play, Terminal } from "lucide-react";
import { api } from "../../shared/api/client";
import { AnalysisJob } from "../../shared/types";

interface RepositoryOnboardingProps {
  onAnalysisComplete: (job: AnalysisJob) => void;
}

const STAGES = [
  { id: "CLONING", label: "Git Clone & Sandbox", desc: "Shallow clone & safety checks" },
  { id: "INDEXING", label: "AST Indexing", desc: "Language detection & file tree" },
  { id: "STATIC_ANALYSIS", label: "Static Analysis", desc: "Complexity & rule evaluation" },
  { id: "DEFECT_PREDICTION", label: "ML Defect Risk", desc: "XGBoost & SHAP attribution" },
  { id: "AGGREGATING", label: "Quality Scorecard", desc: "4 pillar aggregation" },
];

export const RepositoryOnboarding: React.FC<RepositoryOnboardingProps> = ({ onAnalysisComplete }) => {
  const [repoUrl, setRepoUrl] = useState("https://github.com/octocat/Hello-World.git");
  const [branch, setBranch] = useState("master");
  const [isLoading, setIsLoading] = useState(false);
  const [activeJob, setActiveJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    setLogs(["[SYSTEM] Initializing repository security check..."]);

    try {
      // 1. Register or get repository
      setLogs((prev) => [...prev, `[SSRF] Validating target URL: ${repoUrl}`]);
      const repo = await api.createRepository(repoUrl, undefined, branch);
      setLogs((prev) => [...prev, `[REPO] Registered repository ID: ${repo.id}`]);

      // 2. Trigger analysis
      setLogs((prev) => [...prev, `[DISPATCH] Triggering analysis pipeline on branch '${branch}'...`]);
      const job = await api.triggerAnalysis(repo.id, branch);
      setActiveJob(job);
      setLogs((prev) => [...prev, `[JOB] Job dispatched: ${job.id}. Listening for pipeline stages...`]);

      // 3. Connect to SSE stream or poll
      listenToEvents(job.id);
    } catch (err: any) {
      setError(err.message || "Failed to start analysis");
      setIsLoading(false);
      setLogs((prev) => [...prev, `[ERROR] ${err.message || "Unknown error"}`]);
    }
  };

  const listenToEvents = (jobId: string) => {
    const eventSource = new EventSource(`/api/v1/events/sse/jobs/${jobId}`);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        setActiveJob((prev) =>
          prev
            ? {
                ...prev,
                current_stage: payload.stage,
                progress_percent: payload.progress,
                status: payload.progress >= 100 ? "COMPLETED" : "STATIC_ANALYSIS",
              }
            : null
        );

        if (payload.message) {
          setLogs((prev) => [...prev, `[${payload.stage}] ${payload.message}`]);
        }

        if (payload.progress >= 100) {
          eventSource.close();
          setIsLoading(false);
          api.getJobStatus(jobId).then((finalJob) => {
            onAnalysisComplete(finalJob);
          });
        }
      } catch (e) {
        console.error("SSE parse error", e);
      }
    };

    eventSource.onerror = () => {
      // Fallback polling if SSE disconnects
      const interval = setInterval(async () => {
        try {
          const current = await api.getJobStatus(jobId);
          setActiveJob(current);
          if (current.status === "COMPLETED" || current.status === "FAILED") {
            clearInterval(interval);
            setIsLoading(false);
            if (current.status === "COMPLETED") {
              onAnalysisComplete(current);
            } else {
              setError(current.error_message || "Job failed");
            }
          }
        } catch {
          clearInterval(interval);
          setIsLoading(false);
        }
      }, 2000);
      eventSource.close();
    };
  };

  const getStageIndex = (stage: string) => {
    const idx = STAGES.findIndex((s) => s.id === stage);
    return idx === -1 ? (activeJob?.progress_percent && activeJob.progress_percent > 80 ? 4 : 0) : idx;
  };

  const currentIdx = activeJob ? getStageIndex(activeJob.current_stage) : -1;

  return (
    <div className="space-y-8">
      {/* Onboarding Input Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex items-center space-x-3 mb-4">
          <Github className="w-7 h-7 text-indigo-400" />
          <h2 className="text-xl font-bold text-white">Connect GitHub Repository</h2>
        </div>
        <p className="text-sm text-slate-400 mb-6">
          Provide a public Git URL. The platform will clone in a secure sandbox, index polyglot ASTs, run static analysis rules, evaluate ML defect risks, and generate your quality report.
        </p>

        <form onSubmit={handleStartAnalysis} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Git Repository URL
              </label>
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/user/repository.git"
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Branch
              </label>
              <div className="flex items-center">
                <GitBranch className="w-4 h-4 text-slate-400 mr-2" />
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-rose-950/50 border border-rose-800 rounded-lg text-rose-300 text-sm">
              {error}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex items-center px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900/60 text-white font-medium rounded-lg transition-colors shadow-lg shadow-indigo-500/20"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing Pipeline...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start Full Analysis
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Real-time Pipeline Progress Stepper */}
      {activeJob && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Live Orchestration Pipeline</h3>
              <p className="text-xs text-slate-400">Current Phase: {activeJob.current_stage}</p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-black text-indigo-400">{Math.round(activeJob.progress_percent)}%</span>
              <p className="text-xs text-slate-400">Overall Progress</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-400 h-2.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${Math.max(activeJob.progress_percent, 5)}%` }}
            />
          </div>

          {/* Stepper Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {STAGES.map((s, idx) => {
              const isDone = currentIdx > idx || activeJob.progress_percent >= 100;
              const isCurrent = currentIdx === idx && activeJob.progress_percent < 100;
              return (
                <div
                  key={s.id}
                  className={`p-3 rounded-lg border transition-all ${
                    isDone
                      ? "bg-emerald-950/20 border-emerald-800/60 text-emerald-300"
                      : isCurrent
                      ? "bg-indigo-950/30 border-indigo-500 text-indigo-200 ring-1 ring-indigo-500"
                      : "bg-slate-950 border-slate-800 text-slate-500"
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
                    ) : (
                      <span className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[10px]">
                        {idx + 1}
                      </span>
                    )}
                    <span className="font-semibold text-xs truncate">{s.label}</span>
                  </div>
                  <p className="text-[11px] opacity-75">{s.desc}</p>
                </div>
              );
            })}
          </div>

          {/* Terminal Log Output */}
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-slate-300 max-h-40 overflow-y-auto space-y-1">
            <div className="flex items-center text-slate-500 pb-1 border-b border-slate-800 mb-2">
              <Terminal className="w-3.5 h-3.5 mr-1" />
              <span>Real-Time Worker Events</span>
            </div>
            {logs.map((log, i) => (
              <div key={i} className="leading-relaxed">
                {log}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
