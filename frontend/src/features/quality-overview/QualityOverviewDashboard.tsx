import React, { useMemo, useState } from "react";
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  Award,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Download,
  FileCode,
  Filter,
  Layers,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AnalysisReport, ShapExplanation } from "../../shared/types";
import { CodeReviewViewer } from "../review/CodeReviewViewer";
import { ExportReportModal } from "./ExportReportModal";
import { RadarScorecardViewer } from "./RadarScorecardViewer";

interface QualityOverviewDashboardProps {
  report: AnalysisReport;
  onReset: () => void;
}

const mockTrendData = [
  { commit: "Init", score: 72 },
  { commit: "C-2", score: 74 },
  { commit: "C-3", score: 71 },
  { commit: "C-4", score: 79 },
  { commit: "C-5", score: 83 },
  { commit: "Latest", score: 86 },
];

export const QualityOverviewDashboard: React.FC<QualityOverviewDashboardProps> = ({
  report,
  onReset,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);

  // Phase 4: Defect Prediction Explorer State
  const [defectRiskFilter, setDefectRiskFilter] = useState<string>("ALL");
  const [defectSearchQuery, setDefectSearchQuery] = useState<string>("");
  const [expandedDefects, setExpandedDefects] = useState<Record<string, boolean>>({});

  const toggleExpandDefect = (id: string) => {
    setExpandedDefects((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getGrade = (score: number) => {
    if (score >= 90) return { grade: "A", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };
    if (score >= 80) return { grade: "B", color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/20" };
    if (score >= 70) return { grade: "C", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" };
    if (score >= 60) return { grade: "D", color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/20" };
    return { grade: "F", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" };
  };

  const overallGrade = getGrade(report.overall_score);

  const trendData = useMemo(() => {
    const data = [...mockTrendData];
    data[data.length - 1].score = Math.round(report.overall_score);
    return data;
  }, [report.overall_score]);

  // Filtered issues
  const filteredIssues = useMemo(() => {
    return (report.issues || []).filter((issue) => {
      const matchCat = selectedCategory === "ALL" || issue.category === selectedCategory;
      const matchSev = selectedSeverity === "ALL" || issue.severity === selectedSeverity;
      const matchQuery =
        !searchQuery ||
        issue.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        issue.file_path.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (issue.cwe_id && issue.cwe_id.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchCat && matchSev && matchQuery;
    });
  }, [report.issues, selectedCategory, selectedSeverity, searchQuery]);

  // Ranked file hotspots by cyclomatic complexity and SLOC
  const fileHotspots = useMemo(() => {
    return [...(report.file_metrics || [])]
      .sort((a, b) => b.cyclomatic_complexity - a.cyclomatic_complexity)
      .slice(0, 8);
  }, [report.file_metrics]);

  // Phase 4: Defect Prediction Summary Statistics
  const defectSummary = useMemo(() => {
    const preds = report.defect_predictions || [];
    const total = preds.length;
    const critical = preds.filter((p) => p.risk_tier === "CRITICAL").length;
    const high = preds.filter((p) => p.risk_tier === "HIGH").length;
    const moderate = preds.filter((p) => p.risk_tier === "MODERATE").length;
    const low = preds.filter((p) => p.risk_tier === "LOW").length;
    const avgProb = total > 0 ? preds.reduce((acc, p) => acc + p.defect_probability, 0) / total : 0;
    const sorted = [...preds].sort((a, b) => b.defect_probability - a.defect_probability);
    return {
      total,
      critical,
      high,
      moderate,
      low,
      avgProb: Math.round(avgProb * 100),
      highestRiskFile: sorted[0]?.file_path,
      highestRiskProb: sorted[0] ? Math.round(sorted[0].defect_probability * 100) : 0,
    };
  }, [report.defect_predictions]);

  // Phase 4: Filtered Defect Predictions
  const filteredDefects = useMemo(() => {
    return (report.defect_predictions || [])
      .filter((dp) => {
        const matchTier = defectRiskFilter === "ALL" || dp.risk_tier === defectRiskFilter;
        const matchQuery =
          !defectSearchQuery ||
          dp.file_path.toLowerCase().includes(defectSearchQuery.toLowerCase());
        return matchTier && matchQuery;
      })
      .sort((a, b) => b.defect_probability - a.defect_probability);
  }, [report.defect_predictions, defectRiskFilter, defectSearchQuery]);

  return (
    <div className="space-y-8">
      {/* Header & Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Static Analysis Complete
            </span>
            {report.summary_metadata?.project_types && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                {report.summary_metadata.project_types.join(", ")}
              </span>
            )}
          </div>
          <h2 className="text-xl font-bold text-white">Quality Assessment Report</h2>
          <p className="text-xs text-slate-400">
            Total Files: {report.total_files} | SLOC: {report.total_lines_of_code} | Functions: {report.total_functions} | Tech Debt: {report.technical_debt_minutes} min ({Math.round(report.technical_debt_minutes / 60)}h)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsExportModalOpen(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 mr-1.5" />
            Export Report
          </button>
          <button
            onClick={onReset}
            className="inline-flex items-center px-4 py-2 border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-medium rounded-lg transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            Analyze Another Repository
          </button>
        </div>
      </div>

      {/* Top Grid: Score Gauge & 4 Category Pillars */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Overall Quality Score Gauge Card */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col items-center justify-center text-center">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Overall Quality Score
          </span>
          <div className="relative w-44 h-44 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                className="text-slate-800 stroke-current"
                strokeWidth="8"
                fill="transparent"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                className={`${overallGrade.color} stroke-current transition-all duration-1000 ease-out`}
                strokeWidth="8"
                strokeDasharray={2 * Math.PI * 40}
                strokeDashoffset={2 * Math.PI * 40 * (1 - report.overall_score / 100)}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-4xl font-black ${overallGrade.color}`}>
                {Math.round(report.overall_score)}
              </span>
              <span className="text-xs font-bold text-slate-400">/ 100</span>
              <span className={`text-xs px-2 py-0.5 mt-1 rounded font-bold ${overallGrade.bg} ${overallGrade.color}`}>
                Grade {overallGrade.grade}
              </span>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-4 max-w-xs">
            Composite rating calculated from static code metrics, architectural violations, security patterns, and ML defect risk.
          </p>
        </div>

        {/* 4 Pillars Grid */}
        <div className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Maintainability */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
                  <FileCode className="w-5 h-5" />
                </div>
                <span className="text-sm font-semibold text-slate-200">Maintainability</span>
              </div>
              <span className={`text-lg font-bold ${getGrade(report.maintainability_score).color}`}>
                {Math.round(report.maintainability_score)}
              </span>
            </div>
            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
              <div
                className="bg-indigo-500 h-2 rounded-full"
                style={{ width: `${report.maintainability_score}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">
              McCabe cyclomatic complexity & Halstead volume metrics.
            </p>
          </div>

          {/* Security */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <span className="text-sm font-semibold text-slate-200">Security</span>
              </div>
              <span className={`text-lg font-bold ${getGrade(report.security_score).color}`}>
                {Math.round(report.security_score)}
              </span>
            </div>
            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
              <div
                className="bg-emerald-500 h-2 rounded-full"
                style={{ width: `${report.security_score}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Vulnerability scans, hardcoded secrets & CWE defense.
            </p>
          </div>

          {/* Testing */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-sky-500/10 rounded-lg text-sky-400">
                  <CheckCircle className="w-5 h-5" />
                </div>
                <span className="text-sm font-semibold text-slate-200">Testing</span>
              </div>
              <span className={`text-lg font-bold ${getGrade(report.testing_score).color}`}>
                {Math.round(report.testing_score)}
              </span>
            </div>
            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
              <div
                className="bg-sky-500 h-2 rounded-full"
                style={{ width: `${report.testing_score}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Test suite ratio and automated coverage footprint.
            </p>
          </div>

          {/* Architecture */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                  <Layers className="w-5 h-5" />
                </div>
                <span className="text-sm font-semibold text-slate-200">Architecture</span>
              </div>
              <span className={`text-lg font-bold ${getGrade(report.architecture_score).color}`}>
                {Math.round(report.architecture_score)}
              </span>
            </div>
            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
              <div
                className="bg-purple-500 h-2 rounded-full"
                style={{ width: `${report.architecture_score}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Coupling between objects & modular dependency health.
            </p>
          </div>
        </div>
      </div>

      {/* Phase 6: Multi-Dimensional Radar Scorecard & Prioritized Roadmap */}
      <RadarScorecardViewer report={report} />

      {/* Historical Trend Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">Quality Score Trend Across Revisions</h3>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="commit" stroke="#64748b" textAnchor="middle" />
              <YAxis stroke="#64748b" domain={[50, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#6366f1"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorScore)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Interactive Code Smells & Security Findings Explorer */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">
              Code Smells & Vulnerability Findings ({filteredIssues.length} of {report.issues?.length || 0})
            </h3>
          </div>

          {/* Search bar */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search file, smell, CWE..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mr-2">
            <Filter className="w-3.5 h-3.5" />
            <span>Category:</span>
          </div>
          {["ALL", "SECURITY", "CODE_SMELL", "MAINTAINABILITY", "ARCHITECTURE"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                selectedCategory === cat
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {cat.replace("_", " ")}
            </button>
          ))}

          <div className="h-4 w-px bg-slate-800 mx-2 hidden sm:block" />

          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mr-2">
            <span>Severity:</span>
          </div>
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sev) => (
            <button
              key={sev}
              onClick={() => setSelectedSeverity(sev)}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-colors ${
                selectedSeverity === sev
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Findings List */}
        {filteredIssues.length > 0 ? (
          <div className="divide-y divide-slate-800 border border-slate-800 rounded-lg overflow-hidden">
            {filteredIssues.map((issue) => (
              <div key={issue.id || `${issue.file_path}-${issue.line_start}`} className="p-4 bg-slate-950/50 hover:bg-slate-950 transition-colors space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm text-slate-200">{issue.title}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      {issue.category}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        issue.severity === "CRITICAL"
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          : issue.severity === "HIGH"
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          : "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                      }`}
                    >
                      {issue.severity}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-400">{issue.description}</p>

                {issue.snippet && (
                  <div className="bg-slate-900/80 border border-slate-800 rounded p-2 text-xs font-mono text-indigo-300">
                    {issue.snippet}
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-900 text-[11px] text-slate-500">
                  <div className="flex items-center space-x-3">
                    <span className="font-mono text-indigo-300">{issue.file_path}:{issue.line_start}</span>
                    {issue.cwe_id && (
                      <span className="text-slate-400 font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                        {issue.cwe_id}
                      </span>
                    )}
                  </div>
                  {issue.remediation && (
                    <span className="text-emerald-400 font-medium">Fix: {issue.remediation}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center bg-slate-950 rounded-lg border border-slate-800 text-slate-400 text-sm">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            No findings matching selected category and severity filters.
          </div>
        )}
      </div>

      {/* File Hotspots & Metric Ranking Table */}
      {fileHotspots.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white">Repository File Hotspots (Complexity & SLOC)</h3>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">File Path</th>
                  <th className="py-2.5 px-3">SLOC</th>
                  <th className="py-2.5 px-3">Max Cyclomatic CC</th>
                  <th className="py-2.5 px-3">Cognitive CC</th>
                  <th className="py-2.5 px-3">Functions</th>
                  <th className="py-2.5 px-3">Maintainability</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {fileHotspots.map((m) => (
                  <tr key={m.file_path} className="hover:bg-slate-950/60 transition-colors">
                    <td className="py-2.5 px-3 font-mono text-indigo-300">{m.file_path}</td>
                    <td className="py-2.5 px-3">{m.sloc}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`font-semibold ${
                          m.cyclomatic_complexity > 15
                            ? "text-rose-400"
                            : m.cyclomatic_complexity > 10
                            ? "text-amber-400"
                            : "text-slate-300"
                        }`}
                      >
                        {m.cyclomatic_complexity}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">{m.cognitive_complexity}</td>
                    <td className="py-2.5 px-3">{m.function_count}</td>
                    <td className="py-2.5 px-3">
                      <span className={`font-semibold ${getGrade(m.maintainability_index).color}`}>
                        {Math.round(m.maintainability_index)}/100
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Phase 4: Machine Learning Defect Risk & TreeSHAP Explainability */}
      {report.defect_predictions && report.defect_predictions.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
          {/* Section Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <Award className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">
                  Machine Learning Defect Risk & TreeSHAP Explainability
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Sparkles className="w-3 h-3 mr-1" />
                  TreeSHAP v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Predicts future defect proneness based on NASA MDP & PROMISE software benchmarks, explaining key risk drivers.
              </p>
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              <span>Avg Risk: <strong className="text-white">{defectSummary.avgProb}%</strong></span>
            </div>
          </div>

          {/* Risk Tier Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950 p-3.5 rounded-lg border border-rose-500/30">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-rose-400">Critical Risk (≥75%)</span>
                <AlertOctagon className="w-4 h-4 text-rose-400" />
              </div>
              <div className="mt-2 flex items-baseline space-x-2">
                <span className="text-2xl font-bold text-rose-300">{defectSummary.critical}</span>
                <span className="text-[11px] text-slate-400">
                  ({defectSummary.total > 0 ? Math.round((defectSummary.critical / defectSummary.total) * 100) : 0}%)
                </span>
              </div>
            </div>

            <div className="bg-slate-950 p-3.5 rounded-lg border border-amber-500/30">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-amber-400">High Risk (50-74%)</span>
                <AlertTriangle className="w-4 h-4 text-amber-400" />
              </div>
              <div className="mt-2 flex items-baseline space-x-2">
                <span className="text-2xl font-bold text-amber-300">{defectSummary.high}</span>
                <span className="text-[11px] text-slate-400">
                  ({defectSummary.total > 0 ? Math.round((defectSummary.high / defectSummary.total) * 100) : 0}%)
                </span>
              </div>
            </div>

            <div className="bg-slate-950 p-3.5 rounded-lg border border-sky-500/30">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-sky-400">Moderate (25-49%)</span>
                <Activity className="w-4 h-4 text-sky-400" />
              </div>
              <div className="mt-2 flex items-baseline space-x-2">
                <span className="text-2xl font-bold text-sky-300">{defectSummary.moderate}</span>
                <span className="text-[11px] text-slate-400">
                  ({defectSummary.total > 0 ? Math.round((defectSummary.moderate / defectSummary.total) * 100) : 0}%)
                </span>
              </div>
            </div>

            <div className="bg-slate-950 p-3.5 rounded-lg border border-emerald-500/30">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400">Low Risk (&lt;25%)</span>
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="mt-2 flex items-baseline space-x-2">
                <span className="text-2xl font-bold text-emerald-300">{defectSummary.low}</span>
                <span className="text-[11px] text-slate-400">
                  ({defectSummary.total > 0 ? Math.round((defectSummary.low / defectSummary.total) * 100) : 0}%)
                </span>
              </div>
            </div>
          </div>

          {/* Defect Search & Risk Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center space-x-1.5 text-xs text-slate-400 mr-2">
                <Filter className="w-3.5 h-3.5" />
                <span>Risk Tier:</span>
              </div>
              {["ALL", "CRITICAL", "HIGH", "MODERATE", "LOW"].map((tier) => (
                <button
                  key={tier}
                  onClick={() => setDefectRiskFilter(tier)}
                  className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                    defectRiskFilter === tier
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
                  }`}
                >
                  {tier}
                </button>
              ))}
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={defectSearchQuery}
                onChange={(e) => setDefectSearchQuery(e.target.value)}
                placeholder="Search defect module..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Defect Predictions List */}
          {filteredDefects.length > 0 ? (
            <div className="space-y-3">
              {filteredDefects.map((dp) => {
                const isExpanded = expandedDefects[dp.id] || dp.risk_tier === "CRITICAL";
                const explanation = (dp.shap_factors as ShapExplanation) || {};
                const factors = explanation.factors || [];

                return (
                  <div
                    key={dp.id}
                    className="border border-slate-800 rounded-xl bg-slate-950/70 overflow-hidden hover:border-slate-700 transition-colors"
                  >
                    {/* Header Row */}
                    <div
                      onClick={() => toggleExpandDefect(dp.id)}
                      className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer select-none bg-slate-950/90"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs font-semibold text-indigo-300">
                            {dp.file_path}
                          </span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              dp.risk_tier === "CRITICAL"
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                : dp.risk_tier === "HIGH"
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                : dp.risk_tier === "MODERATE"
                                ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                                : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            }`}
                          >
                            {dp.risk_tier} RISK
                          </span>
                        </div>
                        {explanation.summary && (
                          <p className="text-xs text-slate-400 max-w-2xl">
                            {explanation.summary}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="flex items-baseline space-x-1">
                            <span className="text-xs text-slate-400 font-medium">Defect Probability:</span>
                            <span
                              className={`text-sm font-black ${
                                dp.risk_tier === "CRITICAL"
                                  ? "text-rose-400"
                                  : dp.risk_tier === "HIGH"
                                  ? "text-amber-400"
                                  : dp.risk_tier === "MODERATE"
                                  ? "text-sky-400"
                                  : "text-emerald-400"
                              }`}
                            >
                              {Math.round(dp.defect_probability * 100)}%
                            </span>
                          </div>
                          <span className="text-[10px] text-slate-500">
                            Model: {dp.model_version}
                          </span>
                        </div>
                        <button className="p-1 hover:bg-slate-800 rounded text-slate-400 transition-colors">
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* TreeSHAP Explanation Drawer */}
                    {isExpanded && factors.length > 0 && (
                      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40 space-y-4">
                        <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800/60">
                          <span className="font-semibold text-slate-300">
                            TreeSHAP Feature Attributions (Local Shapley Values)
                          </span>
                          <span className="text-[11px] text-slate-500">
                            Base Value E[y]: {explanation.base_value ? Math.round(explanation.base_value * 100) : 18}%
                          </span>
                        </div>

                        {/* SHAP Factors Bars */}
                        <div className="grid grid-cols-1 gap-2.5">
                          {factors.slice(0, 6).map((f) => {
                            const isPositive = f.impact_direction === "INCREASES_RISK";
                            return (
                              <div
                                key={f.feature_name}
                                className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/60 space-y-1.5"
                              >
                                <div className="flex items-center justify-between text-xs">
                                  <div className="flex items-center space-x-2">
                                    <span className="font-medium text-slate-200">
                                      {f.display_name}
                                    </span>
                                    <span className="text-[10px] text-slate-500 font-mono">
                                      (value: {f.feature_value})
                                    </span>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <span
                                      className={`text-[11px] font-bold font-mono ${
                                        isPositive ? "text-rose-400" : "text-emerald-400"
                                      }`}
                                    >
                                      {isPositive ? "+" : ""}
                                      {f.shap_value.toFixed(3)} ({f.percentage}%)
                                    </span>
                                    <span
                                      className={`text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase ${
                                        isPositive
                                          ? "bg-rose-500/10 text-rose-400"
                                          : "bg-emerald-500/10 text-emerald-400"
                                      }`}
                                    >
                                      {isPositive ? "Elevates Risk" : "Reduces Risk"}
                                    </span>
                                  </div>
                                </div>

                                {/* Visual Horizontal Bar */}
                                <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                                  <div
                                    className={`h-1.5 rounded-full transition-all duration-500 ${
                                      isPositive ? "bg-rose-500" : "bg-emerald-500"
                                    }`}
                                    style={{ width: `${Math.min(100, Math.max(8, f.percentage * 2))}%` }}
                                  />
                                </div>

                                {f.remediation && isPositive && f.percentage > 15 && (
                                  <p className="text-[11px] text-amber-300/90 pt-0.5">
                                    💡 <strong>Remediation:</strong> {f.remediation}
                                  </p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-8 text-center bg-slate-950 rounded-lg border border-slate-800 text-slate-400 text-sm">
              <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              No defect predictions matching selected risk tier and search criteria.
            </div>
          )}
        </div>
      )}

      {/* Phase 5: Automated Code Review Comments & Suggested Patches */}
      {report.review_comments && report.review_comments.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <CodeReviewViewer comments={report.review_comments} />
        </div>
      )}

      {/* Phase 7: Export Report Modal */}
      <ExportReportModal
        report={report}
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
      />
    </div>
  );
};
