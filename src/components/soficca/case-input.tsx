'use client';

import { useMemo, useState } from 'react';

import { cn } from '@/lib/utils';
import type { CardioScenario, CardioScenarioId } from '@/lib/cardio-types';

type CaseInputProps = {
  scenarios: CardioScenario[];
  selectedScenarioId: CardioScenarioId;
  payloadJson: string;
  statusMessage: string;
  onScenarioChange: (scenarioId: CardioScenarioId) => void;
  onPayloadChange: (payloadJson: string) => void;
  onRunEvaluation: () => void;
  onReset: () => void;
  isLoading: boolean;
};

export function CaseInput({
  scenarios,
  selectedScenarioId,
  payloadJson,
  statusMessage,
  onScenarioChange,
  onPayloadChange,
  onRunEvaluation,
  onReset,
  isLoading,
}: CaseInputProps) {
  const [showPayload, setShowPayload] = useState(true);

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? scenarios[0],
    [scenarios, selectedScenarioId]
  );

  return (
    <div className="flex h-full flex-col bg-card/30">
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Case Intake</h2>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        <IntakeSection label="Scenario">
          <div className="flex flex-wrap gap-1.5">
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => onScenarioChange(scenario.id)}
                className={cn(
                  'rounded-sm px-2.5 py-1 text-xs font-medium transition-colors',
                  selectedScenarioId === scenario.id
                    ? 'bg-foreground text-background'
                    : 'bg-secondary/60 text-secondary-foreground hover:bg-secondary'
                )}
              >
                {scenario.label}
              </button>
            ))}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground/70">
            Scenario selection preloads input only. Evaluation runs only when you click Run Evaluation.
          </p>
        </IntakeSection>

        <IntakeSection label="Selected Scenario">
          <div className="rounded-sm bg-input/50 px-3 py-2 text-xs text-foreground">{selectedScenario.label}</div>
        </IntakeSection>

        <IntakeSection label="Status">
          <p className="text-[11px] leading-relaxed text-muted-foreground/80">{statusMessage}</p>
        </IntakeSection>

        <div className="border-t border-border/50 pt-4">
          <button
            onClick={() => setShowPayload(!showPayload)}
            className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50 transition-colors hover:text-muted-foreground"
          >
            <span className={cn('transition-transform', showPayload && 'rotate-90')}>{'▸'}</span>
            Input Payload JSON
          </button>
          {showPayload && (
            <textarea
              className="mt-2 min-h-56 w-full resize-y rounded-md bg-background/50 p-3 font-mono text-[10px] text-muted-foreground/90 outline-none ring-1 ring-border focus:ring-2"
              spellCheck={false}
              value={payloadJson}
              onChange={(event) => onPayloadChange(event.target.value)}
            />
          )}
        </div>
      </div>

      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <button
            onClick={onRunEvaluation}
            disabled={isLoading}
            className={cn(
              'flex-1 rounded-sm bg-foreground px-4 py-2 text-xs font-semibold text-background transition-colors',
              isLoading ? 'cursor-not-allowed opacity-50' : 'hover:bg-foreground/90'
            )}
          >
            {isLoading ? 'Evaluating...' : 'Run Evaluation'}
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
  );
}

function IntakeSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/80">{label}</h3>
      {children}
    </section>
  );
}
