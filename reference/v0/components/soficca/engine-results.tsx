"use client"

import { useState, useEffect } from "react"
import type { EngineResult, RouteDecision, UrgencyLevel } from "@/lib/soficca-types"
import { cn } from "@/lib/utils"

interface EngineResultsProps {
  result: EngineResult | null
  isLoading: boolean
}

export function EngineResults({ result, isLoading }: EngineResultsProps) {
  if (isLoading) {
    return <LoadingState />
  }

  if (!result) {
    return <EmptyState />
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Engine Output
        </h2>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-6">
        {/* Case Summary - Compact executive summary */}
        <CaseSummaryBlock summary={result.caseSummary} />

        {/* Decision Summary - Dominant Card */}
        <DecisionSummaryCard summary={result.decisionSummary} />

        {/* Safety Status */}
        <SafetyStatusCard status={result.safetyStatus} />

        {/* Operational Next Steps */}
        <OperationalNextStepsCard steps={result.operationalNextSteps} />

        {/* Technical Trace */}
        <TechnicalTraceCard trace={result.technicalTrace} />
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Engine Output
        </h2>
      </div>
      <div className="flex flex-1 items-center justify-center">
        <div className="space-y-4 text-center">
          <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-border border-t-foreground" />
          <p className="text-xs text-muted-foreground">Processing evaluation...</p>
        </div>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Engine Output
        </h2>
      </div>
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="max-w-xs space-y-4 text-center">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-secondary/50">
            <svg
              className="h-5 w-5 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">
            Select a scenario and run evaluation to generate routing decision
          </p>
        </div>
      </div>
    </div>
  )
}

function CaseSummaryBlock({ summary }: { summary: string }) {
  return (
    <div className="rounded-md border border-border/50 bg-secondary/30 px-4 py-3">
      <div className="flex items-start gap-3">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Case
        </span>
        <p className="flex-1 text-sm leading-relaxed text-foreground/90">
          {summary}
        </p>
      </div>
    </div>
  )
}

function DecisionSummaryCard({
  summary,
}: {
  summary: EngineResult["decisionSummary"]
}) {
  const isEmergency = summary.finalRoute === "EMERGENCY_ROUTE"
  
  return (
    <section
      className={cn(
        "rounded-lg border p-6",
        isEmergency
          ? "border-status-emergency/20 bg-status-emergency/5"
          : "border-border bg-card"
      )}
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex-1 space-y-1">
          <h3
            className={cn(
              "text-xl font-semibold tracking-tight",
              isEmergency ? "text-foreground" : "text-foreground"
            )}
          >
            {summary.title}
          </h3>
        </div>
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-2">
        <UrgencyBadge urgency={summary.urgency} />
        <RouteBadge route={summary.finalRoute} />
      </div>

      <p className="text-sm leading-relaxed text-muted-foreground">
        {summary.rationale}
      </p>

      {summary.preliminaryRoute &&
        summary.preliminaryRoute !== summary.finalRoute && (
          <div className="mt-4 flex items-center gap-3 border-t border-border/50 pt-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="text-muted-foreground/60">Preliminary</span>
              <span className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-[10px]">
                {formatRoute(summary.preliminaryRoute)}
              </span>
            </span>
            <span className="text-muted-foreground/30">→</span>
            <span className="flex items-center gap-1.5">
              <span className="text-muted-foreground/60">Final</span>
              <span className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-[10px]">
                {formatRoute(summary.finalRoute)}
              </span>
            </span>
          </div>
        )}
    </section>
  )
}

function SafetyStatusCard({
  status,
}: {
  status: EngineResult["safetyStatus"]
}) {
  const hasRedFlags = status.redFlagsDetected.length > 0
  const isOverride = status.overrideTriggered

  return (
    <section
      className={cn(
        "rounded-lg border p-5",
        isOverride
          ? "border-status-emergency/15 bg-status-emergency/[0.03]"
          : "border-border bg-card"
      )}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Safety Layer
        </h3>
        {isOverride && (
          <span className="rounded-sm bg-status-emergency/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-status-emergency">
            Override Active
          </span>
        )}
      </div>

      {hasRedFlags ? (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1.5">
            {status.redFlagsDetected.map((flag, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 rounded-sm bg-secondary/60 px-2 py-1 text-xs text-foreground/80"
              >
                <span className="h-1 w-1 rounded-full bg-status-emergency/70" />
                {flag}
              </span>
            ))}
          </div>
          {status.overrideReason && (
            <p className="text-xs leading-relaxed text-muted-foreground">
              {status.overrideReason}
            </p>
          )}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          No red flags detected. Safety policy did not require override.
        </p>
      )}
    </section>
  )
}

function OperationalNextStepsCard({
  steps,
}: {
  steps: EngineResult["operationalNextSteps"]
}) {
  const hasContent =
    steps.recommendedActions.length > 0 ||
    steps.missingCriticalInfo.length > 0 ||
    steps.conflictsDetected.length > 0

  return (
    <section className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        Next Steps
      </h3>

      {!hasContent ? (
        <p className="text-xs italic text-muted-foreground">
          No operational steps required.
        </p>
      ) : (
        <div className="space-y-4">
          {steps.recommendedActions.length > 0 && (
            <div className="space-y-2">
              <span className="text-[10px] font-medium uppercase tracking-wider text-accent">
                Recommended Actions
              </span>
              <ul className="space-y-1">
                {steps.recommendedActions.map((action, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs text-foreground/80"
                  >
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent/60" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {steps.missingCriticalInfo.length > 0 && (
            <div className="space-y-2">
              <span className="text-[10px] font-medium uppercase tracking-wider text-status-urgent">
                Missing Data
              </span>
              <ul className="space-y-1">
                {steps.missingCriticalInfo.map((info, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs text-foreground/80"
                  >
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-status-urgent/60" />
                    {info}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {steps.conflictsDetected.length > 0 && (
            <div className="space-y-2">
              <span className="text-[10px] font-medium uppercase tracking-wider text-status-info">
                Conflicts
              </span>
              <ul className="space-y-1">
                {steps.conflictsDetected.map((conflict, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs text-foreground/80"
                  >
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-status-info/60" />
                    {conflict}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

function TechnicalTraceCard({
  trace,
}: {
  trace: EngineResult["technicalTrace"]
}) {
  const [isJsonExpanded, setIsJsonExpanded] = useState(false)
  const [formattedTime, setFormattedTime] = useState<string | null>(null)

  useEffect(() => {
    setFormattedTime(new Date(trace.timestamp).toLocaleTimeString())
  }, [trace.timestamp])

  return (
    <section className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        Trace
      </h3>

      <div className="space-y-4">
        {/* Rules and Policies - Compact chips */}
        <div className="flex flex-wrap gap-x-4 gap-y-3">
          {trace.activatedRules.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] text-muted-foreground/70">Rules</span>
              <div className="flex flex-wrap gap-1">
                {trace.activatedRules.map((rule, i) => (
                  <span
                    key={i}
                    className="rounded-sm bg-secondary/70 px-1.5 py-0.5 font-mono text-[10px] text-secondary-foreground/80"
                  >
                    {rule}
                  </span>
                ))}
              </div>
            </div>
          )}

          {trace.triggeredPolicies.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] text-muted-foreground/70">Policies</span>
              <div className="flex flex-wrap gap-1">
                {trace.triggeredPolicies.map((policy, i) => (
                  <span
                    key={i}
                    className="rounded-sm bg-secondary/70 px-1.5 py-0.5 font-mono text-[10px] text-secondary-foreground/80"
                  >
                    {policy}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Route Summary - Inline */}
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="text-muted-foreground/70">
            Route:{" "}
            <span className="font-mono text-foreground/70">
              {trace.preliminaryRoute ? formatRoute(trace.preliminaryRoute) : "—"}
            </span>
            {trace.preliminaryRoute && trace.preliminaryRoute !== trace.finalRoute && (
              <>
                <span className="mx-1.5 text-muted-foreground/40">→</span>
                <span className="font-mono text-foreground/70">
                  {formatRoute(trace.finalRoute)}
                </span>
              </>
            )}
          </span>
          <span className="text-muted-foreground/40">|</span>
          <span className="text-muted-foreground/70">
            <span className="font-mono text-foreground/70">{trace.evaluationDurationMs}ms</span>
          </span>
          <span className="text-muted-foreground/40">|</span>
          <span className="text-muted-foreground/70">
            <span className="font-mono text-foreground/70">{formattedTime ?? "—"}</span>
          </span>
        </div>

        {/* Raw JSON - Very secondary */}
        <div className="pt-1">
          <button
            onClick={() => setIsJsonExpanded(!isJsonExpanded)}
            className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50 transition-colors hover:text-muted-foreground"
          >
            <span
              className={cn("transition-transform", isJsonExpanded && "rotate-90")}
            >
              {"▸"}
            </span>
            Raw Trace
          </button>
          {isJsonExpanded && (
            <pre className="mt-2 max-h-48 overflow-auto rounded-md bg-background/50 p-3 font-mono text-[10px] text-muted-foreground/70">
              {JSON.stringify(trace, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </section>
  )
}

function UrgencyBadge({ urgency }: { urgency: UrgencyLevel }) {
  const styles: Record<UrgencyLevel, string> = {
    critical: "bg-status-emergency/15 text-status-emergency",
    high: "bg-status-urgent/15 text-status-urgent",
    moderate: "bg-status-info/15 text-status-info",
    low: "bg-status-routine/15 text-status-routine",
    pending: "bg-secondary text-muted-foreground",
  }

  const labels: Record<UrgencyLevel, string> = {
    critical: "Critical",
    high: "High",
    moderate: "Moderate",
    low: "Low",
    pending: "Pending",
  }

  return (
    <span
      className={cn(
        "rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        styles[urgency]
      )}
    >
      {labels[urgency]}
    </span>
  )
}

function RouteBadge({ route }: { route: RouteDecision }) {
  const styles: Record<RouteDecision, string> = {
    EMERGENCY_ROUTE: "border-status-emergency/30 text-status-emergency",
    URGENT_ESCALATION: "border-status-urgent/30 text-status-urgent",
    ROUTINE_REVIEW: "border-status-routine/30 text-status-routine",
    NEEDS_MORE_INFO: "border-status-info/30 text-status-info",
    DEFERRED_PENDING_DATA: "border-border text-muted-foreground",
  }

  return (
    <span
      className={cn(
        "rounded-sm border px-2 py-0.5 font-mono text-[10px] font-medium",
        styles[route]
      )}
    >
      {formatRoute(route)}
    </span>
  )
}

function formatRoute(route: RouteDecision): string {
  return route.replace(/_/g, " ")
}
