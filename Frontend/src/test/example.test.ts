import { describe, it, expect } from "vitest";
import { SUPPORTED_LANGUAGES } from "../lib/api";

describe("example", () => {
  it("should pass", () => {
    expect(true).toBe(true);
  });
});

describe("Supported Languages", () => {
  it("should support Tamil (ta) as a target language", () => {
    const tamil = SUPPORTED_LANGUAGES.find(lang => lang.code === "ta");
    expect(tamil).toBeDefined();
    expect(tamil?.name).toBe("Tamil");
  });
  
  it("should support Hindi (hi) as a target language", () => {
    const hindi = SUPPORTED_LANGUAGES.find(lang => lang.code === "hi");
    expect(hindi).toBeDefined();
    expect(hindi?.name).toBe("Hindi");
  });
});
