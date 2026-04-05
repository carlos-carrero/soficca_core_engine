// Soficca Clinical Decision Layer Types

export type RouteDecision =
  | "NEEDS_MORE_INFO"
  | "ROUTINE_REVIEW"
  | "URGENT_ESCALATION"
  | "EMERGENCY_ROUTE"
  | "DEFERRED_PENDING_DATA"

export type UrgencyLevel = "critical" | "high" | "moderate" | "low" | "pending"

export interface ClinicalInput {
  presentingComplaint: {
    primary: string
    duration: string
    severity: string
  }
  associatedSymptoms: string[]
  vitals: {
    systolicBP: number | null
    diastolicBP: number | null
    heartRate: number | null
    oxygenSaturation: number | null
    temperature: number | null
  }
  cardiovascularHistory: {
    priorMI: boolean
    priorPCI: boolean
    priorCABG: boolean
    knownHF: boolean
    afib: boolean
    otherConditions: string[]
  }
  medicationsAndContext: {
    currentMedications: string[]
    allergies: string[]
    lastMealTime: string | null
    recentProcedures: string | null
  }
}

export interface SafetyStatus {
  overrideTriggered: boolean
  redFlagsDetected: string[]
  overrideReason: string | null
}

export interface OperationalNextSteps {
  recommendedActions: string[]
  missingCriticalInfo: string[]
  conflictsDetected: string[]
}

export interface TechnicalTrace {
  activatedRules: string[]
  triggeredPolicies: string[]
  preliminaryRoute: RouteDecision | null
  finalRoute: RouteDecision
  overrideReason: string | null
  versionMetadata: {
    engineVersion: string
    rulesetVersion: string
    safetyPolicyVersion: string
    contractVersion: string
  }
  timestamp: string
  evaluationDurationMs: number
  rawPayload: object
}

export interface EngineResult {
  caseSummary: string
  decisionSummary: {
    title: string
    rationale: string
    urgency: UrgencyLevel
    finalRoute: RouteDecision
    preliminaryRoute: RouteDecision | null
  }
  safetyStatus: SafetyStatus
  operationalNextSteps: OperationalNextSteps
  technicalTrace: TechnicalTrace
}

export interface DemoScenario {
  id: string
  name: string
  shortName: string
  description: string
  input: ClinicalInput
  result: EngineResult
}
