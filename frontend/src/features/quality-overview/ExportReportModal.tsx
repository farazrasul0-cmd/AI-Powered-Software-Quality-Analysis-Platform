import React, { useState } from "react";
import {
  Check,
  Copy,
  Download,
  ExternalLink,
  FileCode,
  FileText,
  Printer,
  ShieldAlert,
  X,
} from "lucide-react";
import { AnalysisReport } from "../../shared/types";

interface ExportReportModalProps {
  report: AnalysisReport;
  isOpen: boolean;
  onClose: () => void;
}

export const ExportReportModal: React.FC<ExportReportModalProps> = ({
  report,
  isOpen,
  onClose,
}) => {
  const [copiedMd, setCopiedMd] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  if (!isOpen) return null;

  const downloadFile = async (endpoint: string, filename: string, type: string) => {
    try {
      setDownloading(type);
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error("Failed to generate export");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Export download failed:", err);
    } finally {
      setDownloading(null);
    }
  };

  const copyMarkdownToClipboard = async () => {
    try {
      const res = await fetch(`/api/v1/reports/${report.id}/export/markdown`);
      if (res.ok) {
        const text = await res.text();
        await navigator.clipboard.writeText(text);
        setCopiedMd(true);
        setTimeout(() => setCopiedMd(false), 2000);
      }
    } catch (err) {
      console.error("Failed to copy markdown:", err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl p-6 text-slate-100">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Download className="w-5 h-5 text-indigo-400" />
              Export Quality Assessment Report
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Select standardized export formats for CI/CD ingestion, stakeholder review, or PR comments.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Options Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
          {/* 1. SARIF v2.1.0 */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div className="flex items-center gap-2 mb-2 text-indigo-400 font-semibold text-sm">
                <ShieldAlert className="w-4 h-4" />
                <span>OASIS SARIF v2.1.0</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Standard format for native GitHub Code Scanning, GitLab SAST, and Azure DevOps integration.
              </p>
            </div>
            <button
              onClick={() =>
                downloadFile(
                  `/api/v1/reports/${report.id}/export/sarif`,
                  `quality_analysis_${report.id.slice(0, 8)}.sarif`,
                  "sarif"
                )
              }
              disabled={downloading === "sarif"}
              className="mt-4 inline-flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              {downloading === "sarif" ? "Exporting..." : "Download .sarif"}
            </button>
          </div>

          {/* 2. Printable HTML / Save PDF */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div className="flex items-center gap-2 mb-2 text-emerald-400 font-semibold text-sm">
                <Printer className="w-4 h-4" />
                <span>Printable HTML (PDF Ready)</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Self-contained, responsive executive report formatted with print styles for instant PDF saving.
              </p>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() =>
                  downloadFile(
                    `/api/v1/reports/${report.id}/export/html`,
                    `quality_report_${report.id.slice(0, 8)}.html`,
                    "html"
                  )
                }
                disabled={downloading === "html"}
                className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                Download HTML
              </button>
              <a
                href={`/api/v1/reports/${report.id}/export/html`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center p-2 rounded-lg bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 border border-emerald-500/30 transition text-xs"
                title="Open in new tab to print"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          {/* 3. Pull Request Markdown */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div className="flex items-center gap-2 mb-2 text-sky-400 font-semibold text-sm">
                <FileText className="w-4 h-4" />
                <span>PR Markdown Summary</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                GitHub-Flavored Markdown summary formatted for pull request review threads and CI comments.
              </p>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() =>
                  downloadFile(
                    `/api/v1/reports/${report.id}/export/markdown`,
                    `quality_summary_${report.id.slice(0, 8)}.md`,
                    "md"
                  )
                }
                disabled={downloading === "md"}
                className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                Download .md
              </button>
              <button
                onClick={copyMarkdownToClipboard}
                className="inline-flex items-center justify-center px-3 py-2 rounded-lg bg-sky-600/20 text-sky-300 hover:bg-sky-600/30 border border-sky-500/30 transition text-xs font-medium gap-1"
              >
                {copiedMd ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedMd ? "Copied" : "Copy"}
              </button>
            </div>
          </div>

          {/* 4. Complete Raw JSON */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div className="flex items-center gap-2 mb-2 text-amber-400 font-semibold text-sm">
                <FileCode className="w-4 h-4" />
                <span>Full Normalized JSON</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Complete data model export with AST metrics, TreeSHAP Shapley attributions, and reviews.
              </p>
            </div>
            <button
              onClick={() => {
                const dataStr =
                  "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
                const a = document.createElement("a");
                a.href = dataStr;
                a.download = `report_${report.id.slice(0, 8)}_full.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
              }}
              className="mt-4 inline-flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
            >
              <Download className="w-3.5 h-3.5" />
              Download .json
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
