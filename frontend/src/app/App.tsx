import React, { useState } from "react";
import { Cpu, Github, LayoutDashboard, Shield } from "lucide-react";
import { QualityOverviewDashboard } from "../features/quality-overview/QualityOverviewDashboard";
import { RepositoryOnboarding } from "../features/repository-onboarding/RepositoryOnboarding";
import { api } from "../shared/api/client";
import { AnalysisJob, AnalysisReport } from "../shared/types";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"onboarding" | "dashboard">("onboarding");
  const [activeReport, setActiveReport] = useState<AnalysisReport | null>(null);

  const handleAnalysisComplete = async (job: AnalysisJob) => {
    try {
      const report = await api.getReportByJob(job.id);
      setActiveReport(report);
      setActiveTab("dashboard");
    } catch (e) {
      console.error("Could not fetch report for completed job", e);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-indigo-600 to-sky-500 rounded-xl shadow-md shadow-indigo-500/20">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-black text-base tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                Antigravity Quality Platform
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase tracking-wider font-semibold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/50">
                Phase 1 Foundation
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <nav className="flex space-x-1 bg-slate-900 border border-slate-800 p-1 rounded-lg">
              <button
                onClick={() => setActiveTab("onboarding")}
                className={`flex items-center px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  activeTab === "onboarding"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Github className="w-3.5 h-3.5 mr-1.5" />
                Repository
              </button>
              <button
                onClick={() => setActiveTab("dashboard")}
                disabled={!activeReport}
                className={`flex items-center px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  activeTab === "dashboard"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : activeReport
                    ? "text-slate-400 hover:text-white"
                    : "text-slate-600 cursor-not-allowed"
                }`}
              >
                <LayoutDashboard className="w-3.5 h-3.5 mr-1.5" />
                Dashboard {activeReport && "(Active)"}
              </button>
            </nav>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="text-slate-400 hover:text-white transition-colors"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "onboarding" ? (
          <RepositoryOnboarding onAnalysisComplete={handleAnalysisComplete} />
        ) : activeReport ? (
          <QualityOverviewDashboard
            report={activeReport}
            onReset={() => {
              setActiveReport(null);
              setActiveTab("onboarding");
            }}
          />
        ) : (
          <div className="p-12 text-center bg-slate-900 rounded-xl border border-slate-800">
            <Shield className="w-12 h-12 text-slate-500 mx-auto mb-3" />
            <p className="text-slate-300 font-medium">No analysis report loaded yet.</p>
            <button
              onClick={() => setActiveTab("onboarding")}
              className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold rounded-lg"
            >
              Go to Repository Onboarding
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950 py-6 text-center text-xs text-slate-500">
        AI-Powered Software Quality Analysis Platform &copy; 2026 &bull; Architectural Prototype
      </footer>
    </div>
  );
};
