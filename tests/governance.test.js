const assert = require("node:assert/strict");

const {
  GOVERNANCE_PROFILES,
  SAMPLE_POLICY,
  analyzePolicy,
  normalizeText,
  scoreBand
} = require("../app");

function findProfile(report, id) {
  return report.profileResults.find((profile) => profile.id === id);
}

function testSamplePolicyProducesStrongAlignment() {
  const report = analyzePolicy(SAMPLE_POLICY);

  assert.equal(report.profileResults.length, GOVERNANCE_PROFILES.length);
  assert.ok(report.wordCount > 50);

  const euProfile = findProfile(report, "eu-ai-act");
  const isoProfile = findProfile(report, "iso-42001");
  const nistProfile = findProfile(report, "nist-ai-rmf");

  assert.ok(euProfile.score >= 75, `expected EU score to be strong, got ${euProfile.score}`);
  assert.ok(isoProfile.score >= 75, `expected ISO score to be strong, got ${isoProfile.score}`);
  assert.ok(nistProfile.score >= 75, `expected NIST score to be strong, got ${nistProfile.score}`);
  assert.ok(euProfile.dimensions.some((dimension) => dimension.evidence.length > 0));
}

function testSparsePolicyProducesActionableGaps() {
  const report = analyzePolicy("We use AI for productivity and innovation.");
  const euProfile = findProfile(report, "eu-ai-act");

  assert.equal(euProfile.score, 0);
  assert.equal(euProfile.gaps.length, euProfile.totalDimensions);
  assert.match(euProfile.gaps[0].recommendation, /Add|Document|Define|Specify/);
}

function testKeywordMatchingIsCaseAndPunctuationInsensitive() {
  const report = analyzePolicy("The GOVERNANCE committee handles risk appetite, oversight, and documentation.");
  const nistProfile = findProfile(report, "nist-ai-rmf");
  const governDimension = nistProfile.dimensions.find((dimension) => dimension.name === "Govern");

  assert.equal(governDimension.matched, true);
  assert.deepEqual(
    governDimension.matchedKeywords.sort(),
    ["governance", "risk appetite", "documentation", "oversight"].sort()
  );
}

function testUtilityFunctions() {
  assert.equal(normalizeText("AI-Governance, Risk!"), "ai-governance risk");
  assert.equal(scoreBand(82), "Strong");
  assert.equal(scoreBand(55), "Partial");
  assert.equal(scoreBand(12), "Low");
}

testSamplePolicyProducesStrongAlignment();
testSparsePolicyProducesActionableGaps();
testKeywordMatchingIsCaseAndPunctuationInsensitive();
testUtilityFunctions();

console.log("All governance tracker tests passed.");
