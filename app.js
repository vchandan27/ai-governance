(function (root) {
  "use strict";

  const GOVERNANCE_PROFILES = [
    {
      id: "eu-ai-act",
      name: "EU AI Act",
      type: "Regulatory compliance",
      summary:
        "Checks whether the policy anticipates EU AI Act obligations around risk classification, prohibited practices, high-risk systems, transparency, oversight, monitoring, and incident handling.",
      dimensions: [
        {
          name: "Risk classification and scope",
          description: "Defines AI system scope, intended purpose, risk tiers, and applicability triggers.",
          keywords: [
            "risk classification",
            "high-risk",
            "unacceptable risk",
            "intended purpose",
            "ai system inventory",
            "risk tier",
            "classification"
          ],
          recommendation:
            "Add an AI use-case inventory with intended purpose, affected stakeholders, EU market applicability, and risk-tier decision criteria."
        },
        {
          name: "Prohibited practices and safeguards",
          description: "Prevents banned or manipulative AI uses and defines escalation for sensitive use cases.",
          keywords: [
            "prohibited",
            "manipulative",
            "social scoring",
            "biometric identification",
            "emotion recognition",
            "subliminal",
            "vulnerable groups"
          ],
          recommendation:
            "Document prohibited AI practices and require legal review before biometric, emotion, or vulnerable-population use cases proceed."
        },
        {
          name: "Data governance and quality",
          description: "Addresses training, validation, testing data quality, relevance, bias, and provenance.",
          keywords: [
            "data governance",
            "data quality",
            "training data",
            "validation data",
            "testing data",
            "data provenance",
            "bias"
          ],
          recommendation:
            "Define dataset provenance, representativeness, quality checks, bias testing, and retention requirements for AI lifecycle stages."
        },
        {
          name: "Human oversight",
          description: "Requires human-in-the-loop oversight and authority to intervene, override, or stop AI outputs.",
          keywords: [
            "human oversight",
            "human in the loop",
            "override",
            "intervention",
            "manual review",
            "human approval",
            "stop"
          ],
          recommendation:
            "Specify oversight roles, intervention thresholds, override procedures, and training for personnel supervising AI systems."
        },
        {
          name: "Transparency and user notice",
          description: "Explains when users are interacting with AI and how outputs, limitations, or synthetic content are disclosed.",
          keywords: [
            "transparency",
            "user notice",
            "disclosure",
            "explainability",
            "synthetic content",
            "ai-generated",
            "limitations"
          ],
          recommendation:
            "Add user-facing disclosure rules, explainability expectations, and instructions for communicating AI limitations."
        },
        {
          name: "Logging, monitoring, and incidents",
          description: "Maintains logs, post-market monitoring, serious-incident reporting, and corrective actions.",
          keywords: [
            "logging",
            "logs",
            "monitoring",
            "post-market",
            "incident",
            "serious incident",
            "corrective action",
            "conformity"
          ],
          recommendation:
            "Define event logging, performance monitoring, incident severity, regulator notification, and corrective-action workflows."
        }
      ]
    },
    {
      id: "iso-42001",
      name: "ISO/IEC 42001",
      type: "Management system standard",
      summary:
        "Evaluates whether the policy resembles an AI management system with objectives, leadership, roles, lifecycle controls, assurance, and continual improvement.",
      dimensions: [
        {
          name: "AI management system policy",
          description: "Sets AI objectives, organizational context, commitments, and measurable governance outcomes.",
          keywords: [
            "ai management system",
            "management system",
            "policy objectives",
            "organizational context",
            "ai policy",
            "governance objectives"
          ],
          recommendation:
            "State the AI management-system scope, objectives, risk appetite, accountability commitments, and governance metrics."
        },
        {
          name: "Leadership and accountability",
          description: "Defines executive responsibility, governance bodies, control owners, and decision rights.",
          keywords: [
            "leadership",
            "accountability",
            "responsibility",
            "governance committee",
            "control owner",
            "roles",
            "decision rights"
          ],
          recommendation:
            "Name accountable executives, governance forums, RACI-style ownership, approval gates, and escalation paths."
        },
        {
          name: "AI risk and impact assessment",
          description: "Requires risk assessment, impact assessment, treatment plans, and acceptance criteria.",
          keywords: [
            "risk assessment",
            "impact assessment",
            "risk treatment",
            "risk register",
            "acceptance criteria",
            "residual risk"
          ],
          recommendation:
            "Create repeatable AI risk and impact assessment templates with residual-risk approval and treatment tracking."
        },
        {
          name: "Lifecycle controls",
          description: "Controls design, development, validation, deployment, change management, and retirement.",
          keywords: [
            "lifecycle",
            "development",
            "validation",
            "deployment",
            "change management",
            "model retirement",
            "release"
          ],
          recommendation:
            "Add lifecycle gates for design, build, test, deployment, monitoring, change, and decommissioning decisions."
        },
        {
          name: "Suppliers and third parties",
          description: "Covers vendor due diligence, procurement requirements, contracts, and outsourced AI services.",
          keywords: [
            "supplier",
            "vendor",
            "third party",
            "procurement",
            "contract",
            "outsourced",
            "due diligence"
          ],
          recommendation:
            "Include third-party AI due diligence, contract clauses, evidence requirements, and ongoing supplier monitoring."
        },
        {
          name: "Audit and continual improvement",
          description: "Includes internal audit, management review, corrective action, performance evaluation, and improvement.",
          keywords: [
            "internal audit",
            "management review",
            "continual improvement",
            "corrective action",
            "performance evaluation",
            "metrics",
            "nonconformity"
          ],
          recommendation:
            "Define internal audit cadence, management review inputs, nonconformity handling, metrics, and improvement backlog governance."
        }
      ]
    },
    {
      id: "nist-ai-rmf",
      name: "NIST AI RMF",
      type: "Risk-management framework",
      summary:
        "Maps policy language to the NIST AI Risk Management Framework functions: Govern, Map, Measure, and Manage.",
      dimensions: [
        {
          name: "Govern",
          description: "Establishes culture, policies, roles, risk appetite, documentation, and oversight.",
          keywords: [
            "govern",
            "governance",
            "risk appetite",
            "policy",
            "accountability",
            "documentation",
            "oversight"
          ],
          recommendation:
            "Strengthen governance with clear risk appetite, oversight forums, documented decisions, and policy exception handling."
        },
        {
          name: "Map",
          description: "Frames AI context, stakeholders, benefits, harms, assumptions, and operating environment.",
          keywords: [
            "map",
            "context",
            "stakeholder",
            "benefit",
            "harm",
            "assumption",
            "operating environment"
          ],
          recommendation:
            "Require context mapping for each AI use case, including stakeholders, foreseeable harms, benefits, assumptions, and deployment setting."
        },
        {
          name: "Measure",
          description: "Assesses validity, reliability, safety, security, bias, privacy, explainability, and robustness.",
          keywords: [
            "measure",
            "validity",
            "reliability",
            "robustness",
            "fairness",
            "privacy",
            "security",
            "explainability"
          ],
          recommendation:
            "Define measurement protocols for model quality, fairness, robustness, privacy, cybersecurity, explainability, and safety."
        },
        {
          name: "Manage",
          description: "Prioritizes, mitigates, monitors, communicates, and accepts AI risks.",
          keywords: [
            "manage",
            "mitigation",
            "risk treatment",
            "monitoring",
            "risk acceptance",
            "communication",
            "residual risk"
          ],
          recommendation:
            "Add risk prioritization, mitigation ownership, residual-risk acceptance, communication plans, and continuous monitoring."
        },
        {
          name: "Trustworthy AI characteristics",
          description: "Addresses valid, reliable, safe, secure, accountable, transparent, explainable, private, and fair AI.",
          keywords: [
            "trustworthy",
            "safe",
            "secure",
            "accountable",
            "transparent",
            "explainable",
            "private",
            "fair"
          ],
          recommendation:
            "Connect policy requirements to trustworthy-AI characteristics and measurable acceptance criteria for each characteristic."
        }
      ]
    },
    {
      id: "oecd-ai-principles",
      name: "OECD AI Principles",
      type: "Principles and policy baseline",
      summary:
        "Checks alignment with human-centered values, transparency, robustness, accountability, inclusive growth, and responsible stewardship.",
      dimensions: [
        {
          name: "Human-centered values and rights",
          description: "Protects dignity, autonomy, human rights, democratic values, and affected communities.",
          keywords: [
            "human rights",
            "human-centered",
            "dignity",
            "autonomy",
            "democratic values",
            "affected communities",
            "civil liberties"
          ],
          recommendation:
            "Add explicit commitments to human-centered design, rights protection, autonomy, and affected-community consultation."
        },
        {
          name: "Inclusive growth and well-being",
          description: "Considers societal benefit, accessibility, inclusion, sustainability, and shared prosperity.",
          keywords: [
            "inclusive",
            "well-being",
            "accessibility",
            "sustainability",
            "societal benefit",
            "shared prosperity",
            "inclusion"
          ],
          recommendation:
            "Describe how AI initiatives are evaluated for accessibility, inclusion, sustainability, and societal benefit."
        },
        {
          name: "Transparency and responsible disclosure",
          description: "Provides meaningful information about AI systems, outputs, and decision logic.",
          keywords: [
            "transparency",
            "disclosure",
            "meaningful information",
            "explainability",
            "contest",
            "appeal",
            "notice"
          ],
          recommendation:
            "Set disclosure, explanation, contestability, and appeal expectations for people affected by AI decisions."
        },
        {
          name: "Robustness, security, and safety",
          description: "Requires resilient operation, security controls, safety testing, and lifecycle risk management.",
          keywords: [
            "robustness",
            "security",
            "safety",
            "resilience",
            "testing",
            "adversarial",
            "lifecycle risk"
          ],
          recommendation:
            "Add safety and security testing, adversarial resilience checks, fallback plans, and operational monitoring."
        },
        {
          name: "Accountability",
          description: "Assigns responsibility for AI outcomes, oversight, auditability, and remediation.",
          keywords: [
            "accountability",
            "responsibility",
            "auditability",
            "remediation",
            "oversight",
            "redress",
            "traceability"
          ],
          recommendation:
            "Define accountable owners, audit trails, redress mechanisms, and remediation standards for AI-related harm."
        }
      ]
    }
  ];

  const SAMPLE_POLICY = [
    "Our organization maintains an AI system inventory covering intended purpose, business owner, data sources, deployment status, and risk classification.",
    "High-risk use cases require a documented risk assessment, impact assessment, data governance review, privacy review, fairness and bias testing, cybersecurity review, and human oversight before deployment.",
    "The AI governance committee approves exceptions, sets risk appetite, and reviews residual risk for material AI systems.",
    "Model teams must document training data, validation data, performance metrics, explainability limitations, monitoring requirements, and rollback procedures.",
    "Users receive clear notice when they interact with AI-generated content or automated recommendations, and impacted individuals may request manual review.",
    "Suppliers and vendors providing AI capabilities are subject to due diligence, contract controls, audit rights, and ongoing performance evaluation.",
    "Incidents, serious incidents, safety concerns, and policy nonconformities must be logged, escalated, remediated, and reviewed for continual improvement."
  ].join("\n\n");

  function normalizeText(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[\u201c\u201d]/g, '"')
      .replace(/[^a-z0-9\s'"-]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function unique(values) {
    return Array.from(new Set(values));
  }

  function percentage(part, total) {
    if (!total) {
      return 0;
    }
    return Math.round((part / total) * 100);
  }

  function scoreBand(score) {
    if (score >= 75) {
      return "Strong";
    }
    if (score >= 45) {
      return "Partial";
    }
    return "Low";
  }

  function scoreClass(score) {
    if (score >= 75) {
      return "good";
    }
    if (score >= 45) {
      return "partial";
    }
    return "low";
  }

  function splitIntoEvidenceUnits(text) {
    return String(text || "")
      .split(/(?:\n{2,}|(?<=[.!?])\s+)/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function findEvidence(text, keywords, maxSnippets) {
    const snippets = [];
    const evidenceUnits = splitIntoEvidenceUnits(text);

    for (const unit of evidenceUnits) {
      const normalizedUnit = normalizeText(unit);
      const matchedKeywords = keywords.filter((keyword) =>
        normalizedUnit.includes(normalizeText(keyword))
      );

      if (matchedKeywords.length > 0) {
        snippets.push({
          text: unit.length > 260 ? `${unit.slice(0, 257)}...` : unit,
          keywords: unique(matchedKeywords)
        });
      }

      if (snippets.length >= maxSnippets) {
        break;
      }
    }

    return snippets;
  }

  function analyzePolicy(policyText, profiles) {
    const text = String(policyText || "");
    const normalizedPolicy = normalizeText(text);
    const activeProfiles = profiles || GOVERNANCE_PROFILES;

    const profileResults = activeProfiles.map((profile) => {
      const dimensions = profile.dimensions.map((dimension) => {
        const matchedKeywords = unique(
          dimension.keywords.filter((keyword) => normalizedPolicy.includes(normalizeText(keyword)))
        );

        return {
          name: dimension.name,
          description: dimension.description,
          matched: matchedKeywords.length > 0,
          matchedKeywords,
          evidence: findEvidence(text, dimension.keywords, 2),
          recommendation: dimension.recommendation
        };
      });

      const matchedCount = dimensions.filter((dimension) => dimension.matched).length;
      const score = percentage(matchedCount, dimensions.length);

      return {
        id: profile.id,
        name: profile.name,
        type: profile.type,
        summary: profile.summary,
        score,
        band: scoreBand(score),
        matchedCount,
        totalDimensions: dimensions.length,
        dimensions,
        gaps: dimensions
          .filter((dimension) => !dimension.matched)
          .map((dimension) => ({
            dimension: dimension.name,
            recommendation: dimension.recommendation
          }))
      };
    });

    profileResults.sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));

    return {
      generatedAt: new Date().toISOString(),
      wordCount: normalizedPolicy ? normalizedPolicy.split(/\s+/).length : 0,
      profileResults,
      topProfile: profileResults[0] || null,
      averageScore: percentage(
        profileResults.reduce((total, profile) => total + profile.score, 0),
        profileResults.length * 100
      )
    };
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderProfileLibrary(profiles, container) {
    container.innerHTML = profiles
      .map(
        (profile) => `
          <article class="profile-card">
            <span class="profile-tag">${escapeHtml(profile.type)}</span>
            <h3>${escapeHtml(profile.name)}</h3>
            <p>${escapeHtml(profile.summary)}</p>
            <ul class="dimension-list">
              ${profile.dimensions
                .map((dimension) => `<li>${escapeHtml(dimension.name)}</li>`)
                .join("")}
            </ul>
          </article>
        `
      )
      .join("");
  }

  function renderScoreOverview(report, container) {
    container.innerHTML = report.profileResults
      .map(
        (profile) => `
          <article class="score-card">
            <span>${escapeHtml(profile.name)}</span>
            <strong>${profile.score}%</strong>
            <div class="meter ${scoreClass(profile.score)}" aria-hidden="true">
              <span style="width: ${profile.score}%"></span>
            </div>
            <span>${profile.matchedCount}/${profile.totalDimensions} controls matched - ${profile.band}</span>
          </article>
        `
      )
      .join("");
  }

  function renderResults(report, container) {
    container.innerHTML = report.profileResults
      .map((profile) => {
        const dimensions = profile.dimensions
          .map(
            (dimension) => `
              <article class="dimension ${dimension.matched ? "matched" : "missing"}">
                <h4>${dimension.matched ? "Matched" : "Gap"}: ${escapeHtml(dimension.name)}</h4>
                <p>${escapeHtml(dimension.description)}</p>
                ${
                  dimension.matchedKeywords.length
                    ? `<p><strong>Signals:</strong> ${escapeHtml(dimension.matchedKeywords.join(", "))}</p>`
                    : ""
                }
              </article>
            `
          )
          .join("");

        const evidence = profile.dimensions
          .flatMap((dimension) =>
            dimension.evidence.map((item) => ({
              dimension: dimension.name,
              text: item.text,
              keywords: item.keywords
            }))
          )
          .slice(0, 5);

        return `
          <article class="result-card">
            <div class="result-header">
              <div>
                <span class="result-meta">${escapeHtml(profile.type)}</span>
                <h3>${escapeHtml(profile.name)}</h3>
                <p>${escapeHtml(profile.summary)}</p>
              </div>
              <span class="badge">${profile.score}% ${escapeHtml(profile.band)}</span>
            </div>
            <div class="meter ${scoreClass(profile.score)}" aria-label="${escapeHtml(profile.name)} score ${profile.score}%">
              <span style="width: ${profile.score}%"></span>
            </div>
            <div class="dimension-grid">${dimensions}</div>
            <div>
              <h4>Priority gaps</h4>
              ${
                profile.gaps.length
                  ? `<ul class="gap-list">${profile.gaps
                      .slice(0, 4)
                      .map(
                        (gap) =>
                          `<li><strong>${escapeHtml(gap.dimension)}:</strong> ${escapeHtml(gap.recommendation)}</li>`
                      )
                      .join("")}</ul>`
                  : "<p>No first-pass gaps detected for this profile. Validate the evidence with a governance reviewer.</p>"
              }
            </div>
            <div>
              <h4>Evidence snippets</h4>
              ${
                evidence.length
                  ? `<ul class="evidence-list">${evidence
                      .map(
                        (item) =>
                          `<li><strong>${escapeHtml(item.dimension)}</strong><code>${escapeHtml(item.text)}</code></li>`
                      )
                      .join("")}</ul>`
                  : "<p>No supporting snippets detected yet.</p>"
              }
            </div>
          </article>
        `;
      })
      .join("");
  }

  function downloadJson(filename, payload) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function initializeApp() {
    const profileCount = document.querySelector("#profileCount");
    const controlCount = document.querySelector("#controlCount");
    const profileLibrary = document.querySelector("#profileLibrary");
    const form = document.querySelector("#policyForm");
    const fileInput = document.querySelector("#policyFile");
    const fileDrop = document.querySelector(".file-drop");
    const fileName = document.querySelector("#fileName");
    const policyText = document.querySelector("#policyText");
    const resultsSummary = document.querySelector("#resultsSummary");
    const scoreOverview = document.querySelector("#scoreOverview");
    const resultsGrid = document.querySelector("#resultsGrid");
    const downloadReport = document.querySelector("#downloadReport");
    const clearPolicy = document.querySelector("#clearPolicy");
    const loadSamplePolicy = document.querySelector("#loadSamplePolicy");

    let currentReport = null;

    profileCount.textContent = String(GOVERNANCE_PROFILES.length);
    controlCount.textContent = String(
      GOVERNANCE_PROFILES.reduce((total, profile) => total + profile.dimensions.length, 0)
    );
    renderProfileLibrary(GOVERNANCE_PROFILES, profileLibrary);

    function runAnalysis() {
      const text = policyText.value.trim();
      if (!text) {
        resultsSummary.textContent = "Paste or upload policy text before running an analysis.";
        scoreOverview.innerHTML = "";
        resultsGrid.innerHTML = "";
        downloadReport.disabled = true;
        currentReport = null;
        return;
      }

      currentReport = analyzePolicy(text);
      resultsSummary.textContent = `Analyzed ${currentReport.wordCount} words. Top profile: ${currentReport.topProfile.name} (${currentReport.topProfile.score}%). Average alignment: ${currentReport.averageScore}%.`;
      renderScoreOverview(currentReport, scoreOverview);
      renderResults(currentReport, resultsGrid);
      downloadReport.disabled = false;
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runAnalysis();
    });

    fileInput.addEventListener("change", async (event) => {
      const file = event.target.files && event.target.files[0];
      if (!file) {
        return;
      }
      fileName.textContent = file.name;
      policyText.value = await file.text();
      runAnalysis();
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      fileDrop.addEventListener(eventName, (event) => {
        event.preventDefault();
        fileDrop.classList.add("dragging");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      fileDrop.addEventListener(eventName, (event) => {
        event.preventDefault();
        fileDrop.classList.remove("dragging");
      });
    });

    fileDrop.addEventListener("drop", async (event) => {
      const file = event.dataTransfer.files && event.dataTransfer.files[0];
      if (!file) {
        return;
      }
      fileName.textContent = file.name;
      policyText.value = await file.text();
      runAnalysis();
    });

    clearPolicy.addEventListener("click", () => {
      policyText.value = "";
      fileInput.value = "";
      fileName.textContent = "Choose a file or drag it here";
      resultsSummary.textContent = "Run an analysis to see profile scores, evidence, and gap recommendations.";
      scoreOverview.innerHTML = "";
      resultsGrid.innerHTML = "";
      downloadReport.disabled = true;
      currentReport = null;
    });

    loadSamplePolicy.addEventListener("click", () => {
      policyText.value = SAMPLE_POLICY;
      fileName.textContent = "Sample AI policy loaded";
      runAnalysis();
      document.querySelector("#analyze").scrollIntoView({ behavior: "smooth" });
    });

    downloadReport.addEventListener("click", () => {
      if (!currentReport) {
        return;
      }
      downloadJson("ai-governance-report.json", currentReport);
    });
  }

  root.AIGovernanceTracker = {
    GOVERNANCE_PROFILES,
    SAMPLE_POLICY,
    analyzePolicy,
    normalizeText,
    scoreBand
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = root.AIGovernanceTracker;
  }

  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", initializeApp);
  }
})(typeof globalThis !== "undefined" ? globalThis : window);
