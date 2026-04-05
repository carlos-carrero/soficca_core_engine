"use client"

import { useState } from "react"
import type { DemoScenario } from "@/lib/soficca-types"
import { DEMO_SCENARIOS } from "@/lib/demo-scenarios"
import { cn } from "@/lib/utils"

interface CaseInputProps {
  selectedScenario: DemoScenario
  onScenarioChange: (scenario: DemoScenario) => void
  onRunEvaluation: () => void
  onReset: () => void
  isLoading: boolean
}

export function CaseInput({
  selectedScenario,
  onScenarioChange,
  onRunEvaluation,
  onReset,
  isLoading,
}: CaseInputProps) {
  const [showPayload, setShowPayload] = useState(false)

  return (
    <div className="flex h-full flex-col bg-card/30">
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Case Intake
        </h2>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        {/* Scenario Selector */}
        <IntakeSection label="Scenario">
          <div className="flex flex-wrap gap-1.5">
            {DEMO_SCENARIOS.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => onScenarioChange(scenario)}
                className={cn(
                  "rounded-sm px-2.5 py-1 text-xs font-medium transition-colors",
                  selectedScenario.id === scenario.id
                    ? "bg-foreground text-background"
                    : "bg-secondary/60 text-secondary-foreground hover:bg-secondary"
                )}
              >
                {scenario.shortName}
              </button>
            ))}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground/70">
            {selectedScenario.description}
          </p>
        </IntakeSection>

        {/* Presenting Complaint */}
        <IntakeSection label="Presenting Complaint">
          <DataField value={selectedScenario.input.presentingComplaint.primary} />
          <div className="mt-2 flex gap-3">
            <DataFieldInline
              label="Duration"
              value={selectedScenario.input.presentingComplaint.duration}
            />
            <DataFieldInline
              label="Severity"
              value={selectedScenario.input.presentingComplaint.severity}
            />
          </div>
        </IntakeSection>

        {/* Associated Symptoms */}
        <IntakeSection label="Associated Symptoms">
          {selectedScenario.input.associatedSymptoms.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {selectedScenario.input.associatedSymptoms.map((symptom, i) => (
                <span
                  key={i}
                  className="rounded-sm bg-secondary/50 px-2 py-0.5 text-[11px] text-foreground/80"
                >
                  {symptom}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-[11px] italic text-muted-foreground/50">
              None recorded
            </span>
          )}
        </IntakeSection>

        {/* Vitals */}
        <IntakeSection label="Vitals">
          <div className="grid grid-cols-2 gap-2">
            <VitalItem
              label="BP"
              value={
                selectedScenario.input.vitals.systolicBP &&
                selectedScenario.input.vitals.diastolicBP
                  ? `${selectedScenario.input.vitals.systolicBP}/${selectedScenario.input.vitals.diastolicBP}`
                  : null
              }
              unit="mmHg"
            />
            <VitalItem
              label="HR"
              value={selectedScenario.input.vitals.heartRate}
              unit="bpm"
            />
            <VitalItem
              label="SpO2"
              value={selectedScenario.input.vitals.oxygenSaturation}
              unit="%"
            />
            <VitalItem
              label="Temp"
              value={selectedScenario.input.vitals.temperature}
              unit="C"
            />
          </div>
        </IntakeSection>

        {/* Cardiovascular History */}
        <IntakeSection label="CV History">
          <div className="flex flex-wrap gap-1.5">
            <HistoryChip
              label="Prior MI"
              active={selectedScenario.input.cardiovascularHistory.priorMI}
            />
            <HistoryChip
              label="Prior PCI"
              active={selectedScenario.input.cardiovascularHistory.priorPCI}
            />
            <HistoryChip
              label="Prior CABG"
              active={selectedScenario.input.cardiovascularHistory.priorCABG}
            />
            <HistoryChip
              label="Known HF"
              active={selectedScenario.input.cardiovascularHistory.knownHF}
            />
            <HistoryChip
              label="AFib"
              active={selectedScenario.input.cardiovascularHistory.afib}
            />
          </div>
          {selectedScenario.input.cardiovascularHistory.otherConditions.length >
            0 && (
            <div className="mt-2 text-[11px] text-muted-foreground/70">
              Other:{" "}
              <span className="text-foreground/70">
                {selectedScenario.input.cardiovascularHistory.otherConditions.join(", ")}
              </span>
            </div>
          )}
        </IntakeSection>

        {/* Medications & Context */}
        <IntakeSection label="Context">
          {selectedScenario.input.medicationsAndContext.currentMedications.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground/60">Medications</span>
              <div className="flex flex-wrap gap-1">
                {selectedScenario.input.medicationsAndContext.currentMedications.map(
                  (med, i) => (
                    <span
                      key={i}
                      className="rounded-sm bg-secondary/50 px-2 py-0.5 text-[11px] text-foreground/80"
                    >
                      {med}
                    </span>
                  )
                )}
              </div>
            </div>
          )}
          {selectedScenario.input.medicationsAndContext.allergies.length > 0 && (
            <div className="mt-2 space-y-1">
              <span className="text-[10px] text-muted-foreground/60">Allergies</span>
              <div className="flex flex-wrap gap-1">
                {selectedScenario.input.medicationsAndContext.allergies.map(
                  (allergy, i) => (
                    <span
                      key={i}
                      className="rounded-sm bg-destructive/10 px-2 py-0.5 text-[11px] text-destructive"
                    >
                      {allergy}
                    </span>
                  )
                )}
              </div>
            </div>
          )}
          {selectedScenario.input.medicationsAndContext.lastMealTime && (
            <div className="mt-2 text-[11px] text-muted-foreground/70">
              Last meal:{" "}
              <span className="text-foreground/70">
                {selectedScenario.input.medicationsAndContext.lastMealTime}
              </span>
            </div>
          )}
          {selectedScenario.input.medicationsAndContext.recentProcedures && (
            <div className="mt-1 text-[11px] text-muted-foreground/70">
              Recent:{" "}
              <span className="text-foreground/70">
                {selectedScenario.input.medicationsAndContext.recentProcedures}
              </span>
            </div>
          )}
          {selectedScenario.input.medicationsAndContext.currentMedications.length === 0 &&
            selectedScenario.input.medicationsAndContext.allergies.length === 0 &&
            !selectedScenario.input.medicationsAndContext.lastMealTime &&
            !selectedScenario.input.medicationsAndContext.recentProcedures && (
              <span className="text-[11px] italic text-muted-foreground/50">
                No context data
              </span>
            )}
        </IntakeSection>

        {/* Payload Preview */}
        <div className="border-t border-border/50 pt-4">
          <button
            onClick={() => setShowPayload(!showPayload)}
            className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50 transition-colors hover:text-muted-foreground"
          >
            <span className={cn("transition-transform", showPayload && "rotate-90")}>
              {"▸"}
            </span>
            Input Payload
          </button>
          {showPayload && (
            <pre className="mt-2 max-h-40 overflow-auto rounded-md bg-background/50 p-3 font-mono text-[10px] text-muted-foreground/70">
              {JSON.stringify(selectedScenario.input, null, 2)}
            </pre>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <button
            onClick={onRunEvaluation}
            disabled={isLoading}
            className={cn(
              "flex-1 rounded-sm bg-foreground px-4 py-2 text-xs font-semibold text-background transition-colors",
              isLoading ? "cursor-not-allowed opacity-50" : "hover:bg-foreground/90"
            )}
          >
            {isLoading ? "Evaluating..." : "Run Evaluation"}
          </button>
          <button
            onClick={onReset}
            disabled={isLoading}
            className="rounded-sm bg-secondary px-3 py-2 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  )
}

function IntakeSection({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <section className="space-y-2">
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/80">
        {label}
      </h3>
      {children}
    </section>
  )
}

function DataField({ value }: { value: string }) {
  return (
    <div className="rounded-sm bg-input/50 px-3 py-2 text-xs text-foreground">
      {value || <span className="italic text-muted-foreground/50">—</span>}
    </div>
  )
}

function DataFieldInline({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-[11px]">
      <span className="text-muted-foreground/60">{label}:</span>{" "}
      <span className="text-foreground/80">
        {value || <span className="italic text-muted-foreground/50">—</span>}
      </span>
    </div>
  )
}

function VitalItem({
  label,
  value,
  unit,
}: {
  label: string
  value: number | string | null
  unit: string
}) {
  return (
    <div className="flex items-baseline justify-between rounded-sm bg-input/30 px-2.5 py-1.5">
      <span className="text-[10px] text-muted-foreground/60">{label}</span>
      {value !== null ? (
        <span className="font-mono text-xs">
          <span className="text-foreground/90">{value}</span>
          <span className="ml-0.5 text-[10px] text-muted-foreground/50">{unit}</span>
        </span>
      ) : (
        <span className="text-[10px] italic text-muted-foreground/40">—</span>
      )}
    </div>
  )
}

function HistoryChip({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 text-[11px]",
        active
          ? "bg-accent/15 text-accent"
          : "bg-secondary/30 text-muted-foreground/50"
      )}
    >
      <span
        className={cn(
          "h-1 w-1 rounded-full",
          active ? "bg-accent" : "bg-muted-foreground/30"
        )}
      />
      {label}
    </span>
  )
}
