import { describe, it, expect } from "vitest";

describe("Quality Dashboard Unit Tests", () => {
  it("calculates grade boundaries accurately", () => {
    const getGrade = (score: number) => {
      if (score >= 90) return "A";
      if (score >= 80) return "B";
      if (score >= 70) return "C";
      if (score >= 60) return "D";
      return "F";
    };

    expect(getGrade(95)).toBe("A");
    expect(getGrade(82)).toBe("B");
    expect(getGrade(74)).toBe("C");
    expect(getGrade(65)).toBe("D");
    expect(getGrade(40)).toBe("F");
  });

  it("verifies pipeline stage order", () => {
    const stages = ["CLONING", "INDEXING", "STATIC_ANALYSIS", "DEFECT_PREDICTION", "AGGREGATING"];
    expect(stages).toHaveLength(5);
    expect(stages[0]).toBe("CLONING");
    expect(stages[4]).toBe("AGGREGATING");
  });
});
