import React, { useState } from "react";
import {
  Check,
  CheckCircle,
  FileCode,
  Filter,
  GitPullRequest,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { api } from "../../shared/api/client";
import { CommentStatus, ReviewComment } from "../../shared/types";

interface CodeReviewViewerProps {
  comments: ReviewComment[];
  onCommentUpdated?: (commentId: string, newStatus: CommentStatus) => void;
}

export const CodeReviewViewer: React.FC<CodeReviewViewerProps> = ({
  comments,
  onCommentUpdated,
}) => {
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [localComments, setLocalComments] = useState<ReviewComment[]>(comments);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const handleStatusUpdate = async (commentId: string, newStatus: CommentStatus) => {
    try {
      setUpdatingId(commentId);
      await api.updateReviewStatus(commentId, newStatus);
      setLocalComments((prev) =>
        prev.map((c) => (c.id === commentId ? { ...c, status: newStatus } : c))
      );
      if (onCommentUpdated) {
        onCommentUpdated(commentId, newStatus);
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setUpdatingId(null);
    }
  };

  const filtered = localComments.filter((c) => {
    const matchStatus = statusFilter === "ALL" || c.status === statusFilter;
    const matchQuery =
      !searchQuery ||
      c.file_path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.comment.toLowerCase().includes(searchQuery.toLowerCase());
    return matchStatus && matchQuery;
  });

  const renderDiffSnippet = (diff: string) => {
    const diffLines = diff.split("\n");
    return (
      <div className="bg-slate-950 rounded-lg p-3 font-mono text-xs overflow-x-auto border border-slate-800">
        <div className="text-[10px] text-slate-500 pb-1 mb-1 border-b border-slate-900 flex items-center justify-between">
          <span>Unified Suggested Patch</span>
          <span>Diff Preview</span>
        </div>
        {diffLines.map((line, idx) => {
          const isAdd = line.startsWith("+") && !line.startsWith("+++");
          const isDel = line.startsWith("-") && !line.startsWith("---");
          const isHunk = line.startsWith("@@");

          let lineClass = "text-slate-300";
          if (isAdd) lineClass = "text-emerald-400 bg-emerald-950/30 px-1 rounded";
          else if (isDel) lineClass = "text-rose-400 bg-rose-950/30 px-1 rounded";
          else if (isHunk) lineClass = "text-indigo-400 font-semibold";

          return (
            <div key={idx} className={lineClass}>
              {line || " "}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <GitPullRequest className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">
              AI-Assisted Code Review & Automated PR Comments
            </h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Sparkles className="w-3 h-3 mr-1" />
              Hybrid Triangulation
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Triangulates static CWE alerts and Phase 4 TreeSHAP risk factors to suppress false alarms and provide actionable patches.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
          <span>Active Comments: <strong className="text-white">{filtered.length}</strong></span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mr-2">
            <Filter className="w-3.5 h-3.5" />
            <span>Status:</span>
          </div>
          {["ALL", "PENDING", "ACCEPTED", "DISMISSED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                statusFilter === st
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search review comments..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Comments List */}
      {filtered.length > 0 ? (
        <div className="space-y-4">
          {filtered.map((comment) => {
            const isUpdating = updatingId === comment.id;

            return (
              <div
                key={comment.id}
                className={`p-5 rounded-xl border transition-all ${
                  comment.status === "ACCEPTED"
                    ? "bg-emerald-950/10 border-emerald-500/30"
                    : comment.status === "DISMISSED"
                    ? "bg-slate-950/40 border-slate-800 opacity-60"
                    : "bg-slate-950 border-slate-800 hover:border-slate-700 shadow-md"
                } space-y-3.5`}
              >
                {/* Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2 font-mono text-xs">
                    <span className="text-indigo-400 flex items-center">
                      <FileCode className="w-3.5 h-3.5 mr-1" />
                      {comment.file_path}:{comment.line_number}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        comment.status === "ACCEPTED"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : comment.status === "DISMISSED"
                          ? "bg-slate-800 text-slate-400"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {comment.status}
                    </span>

                    {comment.status === "PENDING" && (
                      <div className="flex items-center space-x-1.5">
                        <button
                          disabled={isUpdating}
                          onClick={() => handleStatusUpdate(comment.id, "ACCEPTED")}
                          className="inline-flex items-center px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-medium rounded transition-colors disabled:opacity-50"
                        >
                          <Check className="w-3 h-3 mr-1" />
                          Accept Fix
                        </button>
                        <button
                          disabled={isUpdating}
                          onClick={() => handleStatusUpdate(comment.id, "DISMISSED")}
                          className="inline-flex items-center px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium rounded transition-colors disabled:opacity-50"
                        >
                          <X className="w-3 h-3 mr-1" />
                          Dismiss
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Comment Body */}
                <div className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">
                  {comment.comment}
                </div>

                {/* Suggested Diff Preview */}
                {comment.suggested_patch && renderDiffSnippet(comment.suggested_patch)}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-8 text-center bg-slate-950 rounded-lg border border-slate-800 text-slate-400 text-sm">
          <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
          No AI review comments matching status and filter criteria.
        </div>
      )}
    </div>
  );
};
