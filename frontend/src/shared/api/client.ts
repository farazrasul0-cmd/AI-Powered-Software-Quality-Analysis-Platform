import { AnalysisJob, AnalysisReport, Repository } from "../types";

const BASE_URL = "/api/v1";

export const api = {
  async listRepositories(): Promise<Repository[]> {
    const res = await fetch(`${BASE_URL}/repositories`);
    if (!res.ok) throw new Error("Failed to fetch repositories");
    return res.json();
  },

  async createRepository(url: string, name?: string, default_branch = "main"): Promise<Repository> {
    const res = await fetch(`${BASE_URL}/repositories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, name, default_branch }),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || "Failed to register repository");
    }
    return res.json();
  },

  async triggerAnalysis(repositoryId: string, branch = "main"): Promise<AnalysisJob> {
    const res = await fetch(`${BASE_URL}/analysis/trigger`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repository_id: repositoryId, branch }),
    });
    if (!res.ok) throw new Error("Failed to trigger analysis job");
    return res.json();
  },

  async getJobStatus(jobId: string): Promise<AnalysisJob> {
    const res = await fetch(`${BASE_URL}/analysis/jobs/${jobId}`);
    if (!res.ok) throw new Error("Failed to fetch job status");
    return res.json();
  },

  async getReportByJob(jobId: string): Promise<AnalysisReport> {
    const res = await fetch(`${BASE_URL}/reports/job/${jobId}`);
    if (!res.ok) throw new Error("Failed to fetch report for job");
    return res.json();
  },

  async updateReviewStatus(commentId: string, status: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/reviews/${commentId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error("Failed to update review status");
    return res.json();
  },
};
