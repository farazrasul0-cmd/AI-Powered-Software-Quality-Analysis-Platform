import React, { useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  FileCode,
  FlaskConical,
  Github,
  Radar,
  Search,
  Shield,
  ShieldCheck,
} from "lucide-react";
import { QualityOverviewDashboard } from "../features/quality-overview/QualityOverviewDashboard";
import { RepositoryOnboarding } from "../features/repository-onboarding/RepositoryOnboarding";
import { AcademicBenchmarksViewer } from "../features/benchmarks/AcademicBenchmarksViewer";
import { DEMO_REPORTS } from "../shared/data/demoReports";
import { api } from "../shared/api/client";
import { AnalysisJob, AnalysisReport } from "../shared/types";

type ActiveTab = "scanner" | "scorecard" | "benchmarks";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>("scanner");
  const [activeReport, setActiveReport] = useState<AnalysisReport | null>(null);

  const handleAnalysisComplete = async (job: AnalysisJob) => {
    try {
      const report = await api.getReportByJob(job.id);
      setActiveReport(report);
      setActiveTab("scorecard");
    } catch (e) {
      console.error("Could not fetch report for completed job", e);
    }
  };

  const handleSelectReport = (report: AnalysisReport) => {
    setActiveReport(report);
    setActiveTab("scorecard");
  };

  const handleOpenScorecard = () => {
    if (!activeReport) {
      // If no report has been generated yet in this session, load the default verified report
      setActiveReport(DEMO_REPORTS["fastapi-realworld-example"]);
    }
    setActiveTab("scorecard");
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-gray-100 font-sans selection:bg-pink-500 selection:text-white">
      {/* Top Navbar */}
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl border-b transition-all duration-300 bg-gray-950/90 border-gray-800 shadow-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          {/* Brand / Logo */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setActiveTab("scanner")}
              className="flex items-center gap-2.5 text-left group"
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-pink-500 via-rose-500 to-orange-500 flex items-center justify-center text-white shadow-md shadow-pink-500/20 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                  CodeSentinel AI
                </span>
                <span className="text-[10px] text-gray-400 font-medium -mt-1 hidden sm:inline">
                  Software Quality Platform
                </span>
              </div>
            </button>

            {/* Version Badge */}
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              v1.0.0 (Ready)
            </span>
          </div>

          {/* Functional Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {/* Scanner Tab */}
            <button
              type="button"
              onClick={() => setActiveTab("scanner")}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "scanner"
                  ? "bg-white/10 text-white shadow-sm"
                  : "text-gray-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <Search className="w-3.5 h-3.5 text-pink-400" />
              <span>Scanner</span>
            </button>

            {/* Live Scorecard Tab */}
            <button
              type="button"
              onClick={handleOpenScorecard}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "scorecard"
                  ? "bg-white/10 text-white shadow-sm"
                  : "text-gray-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <Radar className="w-3.5 h-3.5 text-indigo-400" />
              <span>Live Scorecard</span>
            </button>

            {/* Academic Benchmarks Tab */}
            <button
              type="button"
              onClick={() => setActiveTab("benchmarks")}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "benchmarks"
                  ? "bg-white/10 text-white shadow-sm"
                  : "text-gray-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <FlaskConical className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden md:inline">Academic</span> Benchmarks
            </button>

            {/* GitHub External Link */}
            <a
              href="https://github.com/farazrasul0-cmd/CodeSentinel-AI"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold text-gray-300 hover:text-white hover:bg-white/5 transition-all flex items-center gap-1.5"
            >
              <Github className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </nav>
        </div>
      </header>

      {/* Main Content Spacer */}
      <div className="pt-16 flex-grow">
        {activeTab === "scanner" && (
          <RepositoryOnboarding
            onAnalysisComplete={handleAnalysisComplete}
            onSelectReport={handleSelectReport}
            onOpenBenchmarks={() => setActiveTab("benchmarks")}
          />
        )}

        {activeTab === "benchmarks" && (
          <AcademicBenchmarksViewer onBack={() => setActiveTab("scanner")} />
        )}

        {activeTab === "scorecard" && (
          <div className="bg-[#0b0f19] text-white min-h-screen py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="mb-6 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setActiveTab("scanner")}
                  className="inline-flex items-center gap-2 text-xs font-semibold text-gray-300 hover:text-white bg-gray-900/80 hover:bg-gray-800 px-3.5 py-2 rounded-lg transition-colors border border-gray-800"
                >
                  <ArrowLeft className="w-4 h-4" />
                  &larr; Back to Scanner
                </button>

                <div className="flex items-center gap-2 text-xs text-gray-400 font-mono">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  Live Scorecard Mode
                </div>
              </div>

              {activeReport ? (
                <QualityOverviewDashboard
                  report={activeReport}
                  onReset={() => {
                    setActiveReport(null);
                    setActiveTab("scanner");
                  }}
                />
              ) : (
                <div className="p-16 text-center max-w-md mx-auto my-12 bg-gray-900/50 rounded-2xl border border-gray-800">
                  <Shield className="w-12 h-12 text-gray-500 mx-auto mb-3" />
                  <h3 className="text-gray-200 font-bold text-base mb-1">No Active Report Selected</h3>
                  <p className="text-xs text-gray-400 mb-6">
                    Analyze a repository in the Scanner or load an empirical baseline report.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveReport(DEMO_REPORTS["fastapi-realworld-example"]);
                    }}
                    className="px-5 py-2.5 bg-gradient-to-r from-pink-500 to-orange-500 text-white text-xs font-bold rounded-xl shadow-md hover:from-pink-600 hover:to-orange-600 transition"
                  >
                    Load Sample FastAPI Scorecard
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Clean & Functional Open-Source Footer */}
      <footer className="bg-gray-950 border-t border-gray-800 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Left Brand */}
            <div className="flex flex-col sm:flex-row items-center gap-3 text-center sm:text-left">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-pink-500 to-orange-500 flex items-center justify-center text-white shadow">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">
                  CodeSentinel AI &mdash; Academic Research &amp; Software Quality Platform &copy; 2026
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Multi-engine static analysis, TreeSHAP defect forecasting, and hybrid code review
                </p>
              </div>
            </div>

            {/* Right Links */}
            <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-medium">
              <a
                href="https://github.com/farazrasul0-cmd/CodeSentinel-AI"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-gray-400 hover:text-white transition"
              >
                <Github className="w-3.5 h-3.5" />
                <span>GitHub Repository</span>
              </a>

              <a
                href="https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-gray-400 hover:text-white transition"
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>SARIF v2.1.0 Specification</span>
              </a>

              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-gray-400 hover:text-white transition"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Swagger OpenAPI Docs (/docs)</span>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
