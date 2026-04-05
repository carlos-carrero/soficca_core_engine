import type { DemoScenario } from "./soficca-types"

export const VERSION_METADATA = {
  engineVersion: "1.4.2",
  rulesetVersion: "cardio-v1.2.0",
  safetyPolicyVersion: "safety-2.1.0",
  contractVersion: "contract-1.0.3",
}

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: "emergency",
    name: "Emergency Route",
    shortName: "Emergency",
    description: "STEMI presentation with hemodynamic instability",
    input: {
      presentingComplaint: {
        primary: "Crushing chest pain radiating to left arm",
        duration: "45 minutes",
        severity: "10/10",
      },
      associatedSymptoms: [
        "Diaphoresis",
        "Nausea",
        "Dyspnea",
        "Lightheadedness",
      ],
      vitals: {
        systolicBP: 85,
        diastolicBP: 55,
        heartRate: 110,
        oxygenSaturation: 88,
        temperature: 37.2,
      },
      cardiovascularHistory: {
        priorMI: false,
        priorPCI: false,
        priorCABG: false,
        knownHF: false,
        afib: false,
        otherConditions: ["Hypertension", "Hyperlipidemia"],
      },
      medicationsAndContext: {
        currentMedications: ["Lisinopril 10mg", "Atorvastatin 40mg"],
        allergies: [],
        lastMealTime: "3 hours ago",
        recentProcedures: null,
      },
    },
    result: {
      caseSummary: "68-year-old male presenting with acute crushing chest pain, hemodynamic instability, and classic STEMI symptom complex. High-risk profile with critical vitals.",
      decisionSummary: {
        title: "Immediate Emergency Escalation Required",
        rationale:
          "High-risk presentation consistent with acute STEMI. Hemodynamic instability markers triggered safety policy override. Case routed to emergency pathway with highest priority.",
        urgency: "critical",
        finalRoute: "EMERGENCY_ROUTE",
        preliminaryRoute: "URGENT_ESCALATION",
      },
      safetyStatus: {
        overrideTriggered: true,
        redFlagsDetected: [
          "Systolic BP below 90 mmHg",
          "Oxygen saturation below 90%",
          "Classic STEMI symptom complex",
          "Hemodynamic instability pattern",
        ],
        overrideReason:
          "Safety policy escalated from URGENT_ESCALATION to EMERGENCY_ROUTE due to hemodynamic instability markers",
      },
      operationalNextSteps: {
        recommendedActions: [
          "Activate cardiac catheterization lab immediately",
          "Administer dual antiplatelet therapy per protocol",
          "Establish large-bore IV access",
          "Prepare for potential intra-aortic balloon pump",
          "Notify interventional cardiology on-call",
        ],
        missingCriticalInfo: [],
        conflictsDetected: [],
      },
      technicalTrace: {
        activatedRules: [
          "RULE_CHEST_PAIN_SEVERITY_HIGH",
          "RULE_VITAL_SIGNS_CRITICAL",
          "RULE_SYMPTOM_CLUSTER_ACS",
          "RULE_HEMODYNAMIC_INSTABILITY",
        ],
        triggeredPolicies: [
          "POLICY_SAFETY_OVERRIDE_CRITICAL_VITALS",
          "POLICY_ESCALATION_STEMI_PATTERN",
        ],
        preliminaryRoute: "URGENT_ESCALATION",
        finalRoute: "EMERGENCY_ROUTE",
        overrideReason:
          "Safety policy escalated due to critical vital signs and hemodynamic instability",
        versionMetadata: VERSION_METADATA,
        timestamp: new Date().toISOString(),
        evaluationDurationMs: 12,
        rawPayload: {},
      },
    },
  },
  {
    id: "urgent",
    name: "Urgent Escalation",
    shortName: "Urgent",
    description: "Unstable angina with dynamic ECG changes",
    input: {
      presentingComplaint: {
        primary: "Recurrent chest pressure at rest",
        duration: "2 hours, intermittent",
        severity: "7/10",
      },
      associatedSymptoms: ["Shortness of breath", "Fatigue"],
      vitals: {
        systolicBP: 145,
        diastolicBP: 88,
        heartRate: 92,
        oxygenSaturation: 95,
        temperature: 36.8,
      },
      cardiovascularHistory: {
        priorMI: true,
        priorPCI: true,
        priorCABG: false,
        knownHF: false,
        afib: false,
        otherConditions: ["Type 2 Diabetes", "Hypertension"],
      },
      medicationsAndContext: {
        currentMedications: [
          "Aspirin 81mg",
          "Clopidogrel 75mg",
          "Metoprolol 50mg",
          "Metformin 1000mg",
        ],
        allergies: ["Penicillin"],
        lastMealTime: "6 hours ago",
        recentProcedures: "PCI 18 months ago (LAD stent)",
      },
    },
    result: {
      caseSummary: "58-year-old male with prior PCI presenting with recurrent rest chest pressure. Stable vitals but concerning pattern given revascularization history.",
      decisionSummary: {
        title: "High-Priority Escalation Pathway Activated",
        rationale:
          "Pattern consistent with unstable angina in patient with prior revascularization. Risk profile warrants urgent escalation within governed pathway. Routing reflects prior PCI evaluation policy.",
        urgency: "high",
        finalRoute: "URGENT_ESCALATION",
        preliminaryRoute: "URGENT_ESCALATION",
      },
      safetyStatus: {
        overrideTriggered: false,
        redFlagsDetected: [
          "Rest angina pattern",
          "Prior PCI with current symptoms",
        ],
        overrideReason: null,
      },
      operationalNextSteps: {
        recommendedActions: [
          "Serial troponins q3h",
          "Continuous telemetry monitoring",
          "Urgent cardiology consultation",
          "Consider stress testing if troponins negative",
          "Optimize antianginal therapy",
        ],
        missingCriticalInfo: ["Initial troponin result pending"],
        conflictsDetected: [],
      },
      technicalTrace: {
        activatedRules: [
          "RULE_REST_ANGINA_PATTERN",
          "RULE_PRIOR_REVASCULARIZATION",
          "RULE_SYMPTOM_CLUSTER_ACS",
        ],
        triggeredPolicies: ["POLICY_PRIOR_PCI_EVALUATION"],
        preliminaryRoute: "URGENT_ESCALATION",
        finalRoute: "URGENT_ESCALATION",
        overrideReason: null,
        versionMetadata: VERSION_METADATA,
        timestamp: new Date().toISOString(),
        evaluationDurationMs: 8,
        rawPayload: {},
      },
    },
  },
  {
    id: "routine",
    name: "Routine Review",
    shortName: "Routine",
    description: "Stable exertional symptoms, low-risk profile",
    input: {
      presentingComplaint: {
        primary: "Mild chest discomfort with heavy exertion",
        duration: "3 weeks",
        severity: "3/10",
      },
      associatedSymptoms: ["Resolves with rest within 5 minutes"],
      vitals: {
        systolicBP: 128,
        diastolicBP: 78,
        heartRate: 72,
        oxygenSaturation: 98,
        temperature: 36.6,
      },
      cardiovascularHistory: {
        priorMI: false,
        priorPCI: false,
        priorCABG: false,
        knownHF: false,
        afib: false,
        otherConditions: [],
      },
      medicationsAndContext: {
        currentMedications: [],
        allergies: [],
        lastMealTime: null,
        recentProcedures: null,
      },
    },
    result: {
      caseSummary: "45-year-old female with mild exertional chest discomfort over 3 weeks. No cardiac history, stable vitals, symptoms resolve with rest.",
      decisionSummary: {
        title: "Standard Evaluation Pathway Assigned",
        rationale:
          "Stable exertional symptoms with low-risk vital signs and no prior cardiac history. Risk profile within routine parameters. Routed to standard evaluation pathway per policy.",
        urgency: "low",
        finalRoute: "ROUTINE_REVIEW",
        preliminaryRoute: "ROUTINE_REVIEW",
      },
      safetyStatus: {
        overrideTriggered: false,
        redFlagsDetected: [],
        overrideReason: null,
      },
      operationalNextSteps: {
        recommendedActions: [
          "Schedule outpatient stress echocardiogram",
          "Lipid panel and HbA1c",
          "Risk factor modification counseling",
          "Return precautions education",
        ],
        missingCriticalInfo: [],
        conflictsDetected: [],
      },
      technicalTrace: {
        activatedRules: [
          "RULE_STABLE_EXERTIONAL_PATTERN",
          "RULE_LOW_RISK_PROFILE",
        ],
        triggeredPolicies: [],
        preliminaryRoute: "ROUTINE_REVIEW",
        finalRoute: "ROUTINE_REVIEW",
        overrideReason: null,
        versionMetadata: VERSION_METADATA,
        timestamp: new Date().toISOString(),
        evaluationDurationMs: 5,
        rawPayload: {},
      },
    },
  },
  {
    id: "needs-info",
    name: "Needs More Info",
    shortName: "Info Needed",
    description: "Incomplete clinical picture, risk cannot be assessed",
    input: {
      presentingComplaint: {
        primary: "Chest discomfort",
        duration: "Unknown",
        severity: "Unknown",
      },
      associatedSymptoms: [],
      vitals: {
        systolicBP: 132,
        diastolicBP: 82,
        heartRate: 78,
        oxygenSaturation: null,
        temperature: null,
      },
      cardiovascularHistory: {
        priorMI: false,
        priorPCI: false,
        priorCABG: false,
        knownHF: false,
        afib: false,
        otherConditions: [],
      },
      medicationsAndContext: {
        currentMedications: [],
        allergies: [],
        lastMealTime: null,
        recentProcedures: null,
      },
    },
    result: {
      caseSummary: "Adult patient with chest discomfort. Incomplete clinical picture with missing duration, severity, oxygen saturation, and symptom context.",
      decisionSummary: {
        title: "Routing Blocked: Data Threshold Not Met",
        rationale:
          "Insufficient information to satisfy minimum data requirements for risk stratification. Engine policy requires complete clinical picture before routing assignment.",
        urgency: "pending",
        finalRoute: "NEEDS_MORE_INFO",
        preliminaryRoute: null,
      },
      safetyStatus: {
        overrideTriggered: false,
        redFlagsDetected: [],
        overrideReason: null,
      },
      operationalNextSteps: {
        recommendedActions: ["Complete clinical assessment before re-evaluation"],
        missingCriticalInfo: [
          "Oxygen saturation measurement",
          "Symptom character and radiation",
          "Symptom duration and onset",
          "Associated symptom inventory",
          "Cardiovascular history review",
        ],
        conflictsDetected: [],
      },
      technicalTrace: {
        activatedRules: ["RULE_INCOMPLETE_DATA_GATE"],
        triggeredPolicies: ["POLICY_REQUIRE_MINIMUM_DATA"],
        preliminaryRoute: null,
        finalRoute: "NEEDS_MORE_INFO",
        overrideReason: null,
        versionMetadata: VERSION_METADATA,
        timestamp: new Date().toISOString(),
        evaluationDurationMs: 3,
        rawPayload: {},
      },
    },
  },
  {
    id: "deferred",
    name: "Deferred Pending Data",
    shortName: "Deferred",
    description: "Awaiting diagnostic results before final routing",
    input: {
      presentingComplaint: {
        primary: "Atypical chest pain, pleuritic quality",
        duration: "8 hours",
        severity: "5/10",
      },
      associatedSymptoms: ["Pain worse with deep inspiration", "Recent URI symptoms"],
      vitals: {
        systolicBP: 118,
        diastolicBP: 72,
        heartRate: 88,
        oxygenSaturation: 96,
        temperature: 37.8,
      },
      cardiovascularHistory: {
        priorMI: false,
        priorPCI: false,
        priorCABG: false,
        knownHF: false,
        afib: false,
        otherConditions: [],
      },
      medicationsAndContext: {
        currentMedications: ["Ibuprofen PRN"],
        allergies: [],
        lastMealTime: "2 hours ago",
        recentProcedures: null,
      },
    },
    result: {
      caseSummary: "32-year-old male with atypical pleuritic chest pain and recent URI. Low-grade fever, stable vitals. Awaiting troponin and ECG to differentiate etiology.",
      decisionSummary: {
        title: "Routing Deferred: Awaiting Diagnostic Input",
        rationale:
          "Clinical presentation is ambiguous between cardiac and non-cardiac etiology. Final routing contingent on pending diagnostic results per deferral policy.",
        urgency: "moderate",
        finalRoute: "DEFERRED_PENDING_DATA",
        preliminaryRoute: "ROUTINE_REVIEW",
      },
      safetyStatus: {
        overrideTriggered: false,
        redFlagsDetected: [],
        overrideReason: null,
      },
      operationalNextSteps: {
        recommendedActions: [
          "Obtain 12-lead ECG",
          "Draw initial troponin",
          "Re-evaluate once results available",
          "NSAIDs if pericarditis confirmed",
        ],
        missingCriticalInfo: [
          "Troponin result (pending)",
          "ECG interpretation (pending)",
        ],
        conflictsDetected: [
          "Pleuritic quality atypical for ACS but cannot exclude without troponin",
        ],
      },
      technicalTrace: {
        activatedRules: [
          "RULE_ATYPICAL_CHEST_PAIN",
          "RULE_PENDING_DIAGNOSTICS",
          "RULE_PLEURITIC_PATTERN",
        ],
        triggeredPolicies: ["POLICY_DEFER_PENDING_LABS"],
        preliminaryRoute: "ROUTINE_REVIEW",
        finalRoute: "DEFERRED_PENDING_DATA",
        overrideReason: null,
        versionMetadata: VERSION_METADATA,
        timestamp: new Date().toISOString(),
        evaluationDurationMs: 7,
        rawPayload: {},
      },
    },
  },
]

export function getScenarioById(id: string): DemoScenario | undefined {
  return DEMO_SCENARIOS.find((s) => s.id === id)
}
