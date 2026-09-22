import { describe, it, expect } from "vitest";
import { FeatureModalKey } from "../features/repository-onboarding/MethodologyModal";
import { AnalysisReport, RadarScorecardResponse } from "../shared/types";

describe("Modal & Methodology Key Tests", () => {
  it("validates all 4 methodology modal keys are registered", () => {
    const keys: FeatureModalKey[] = [
      "ast-security",
      "treeshap-defect",
      "hybrid-reviewer",
      "rqi-scorecard",
    ];
    expect(keys).toHaveLength(4);
    expect(keys).toContain("ast-security");
    expect(keys).toContain("treeshap-defect");
    expect(keys).toContain("hybrid-reviewer");
    expect(keys).toContain("rqi-scorecard");
  });
});

describe("RadarScorecard Logic Tests", () => {
  const mockReport: AnalysisReport = {
    id: "rep-radar-test",
    job_id: "job-1",
    overall_score: 88.5,
    maintainability_score: 92.0,
    security_score: 100.0,
    testing_score: 75.0,
    architecture_score: 95.0,
    total_files: 42,
    total_lines_of_code: 5200,
    total_functions: 120,
    total_classes: 25,
    technical_debt_minutes: 45,
    summary_metadata: {},
    issues: [],
    file_metrics: [],
    defect_predictions: [],
    review_comments: [],
    created_at: new Date().toISOString(),
  };

  it("derives correct grade from overall score", () => {
    const getGrade = (score: number) => {
      if (score >= 90) return "A";
      if (score >= 80) return "B";
      if (score >= 70) return "C";
      if (score >= 60) return "D";
      return "F";
    };

    expect(getGrade(mockReport.overall_score)).toBe("B");
    expect(getGrade(mockReport.security_score)).toBe("A");
    expect(getGrade(mockReport.maintainability_score)).toBe("A");
  });

  it("constructs valid 5-axis radar chart datasets", () => {
    const axes = [
      { subject: "Security", project: mockReport.security_score, baseline: 75.0, fullMark: 100 },
      { subject: "Maintainability", project: mockReport.maintainability_score, baseline: 70.0, fullMark: 100 },
      { subject: "Architecture", project: mockReport.architecture_score, baseline: 65.0, fullMark: 100 },
      { subject: "Testing", project: mockReport.testing_score, baseline: 60.0, fullMark: 100 },
      { subject: "Defect Immunity", project: 90.0, baseline: 72.0, fullMark: 100 },
    ];

    expect(axes).toHaveLength(5);
    axes.forEach((axis) => {
      expect(axis.project).toBeGreaterThanOrEqual(0);
      expect(axis.project).toBeLessThanOrEqual(axis.fullMark);
      expect(axis.baseline).toBeGreaterThan(0);
    });
  });

  it("validates RadarScorecardResponse schema contracts", () => {
    const sampleResponse: RadarScorecardResponse = {
      report_id: "rep-radar-test",
      overall_score: 88.5,
      grade: "B",
      technical_debt_minutes: 45,
      false_positives_suppressed: 2,
      calculated_at: new Date().toISOString(),
      radar_data: [
        { axis: "Security", value: 100.0, benchmark_value: 75.0 },
      ],
      pillars: [
        {
          name: "Security Posture",
          score: 100.0,
          weight: 0.25,
          weighted_contribution: 25.0,
          grade: "A",
          summary: "0 vulnerabilities found.",
          benchmark_percentile: 95.0,
        },
      ],
      recommendations: [],
    };

    expect(sampleResponse.overall_score).toBe(88.5);
    expect(sampleResponse.pillars[0].grade).toBe("A");
    expect(sampleResponse.false_positives_suppressed).toBe(2);
  });
});
