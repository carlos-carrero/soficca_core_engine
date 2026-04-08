'use client';

import { useMemo, useState } from 'react';

import type { CardioPayload, CardioScenario, CardioScenarioId } from '@/lib/cardio-types';
import { cn } from '@/lib/utils';

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

const scenarioToneById: Record<CardioScenarioId, { active: string; idle: string }> = {
  NEEDS_MORE_INFO: {
    active: 'border border-status-info/30 bg-status-info/18 text-status-info',
    idle: 'border border-status-info/15 bg-status-info/8 text-status-info/80 hover:bg-status-info/14',
  },
  ROUTINE_REVIEW: {
    active: 'border border-status-routine/30 bg-status-routine/18 text-status-routine',
    idle: 'border border-status-routine/15 bg-status-routine/8 text-status-routine/80 hover:bg-status-routine/14',
  },
  URGENT_ESCALATION: {
    active: 'border border-status-urgent/30 bg-status-urgent/18 text-status-urgent',
    idle: 'border border-status-urgent/15 bg-status-urgent/8 text-status-urgent/80 hover:bg-status-urgent/14',
  },
  EMERGENCY_ROUTE: {
    active: 'border border-status-emergency/30 bg-status-emergency/18 text-status-emergency',
    idle: 'border border-status-emergency/15 bg-status-emergency/8 text-status-emergency/80 hover:bg-status-emergency/14',
  },
  DEFERRED_PENDING_DATA: {
    active: 'border border-border bg-secondary text-foreground/90',
    idle: 'border border-border/70 bg-secondary/50 text-muted-foreground hover:bg-secondary/70',
  },
};

function parsePayload(payloadJson: string): CardioPayload | null {
  try {
    const parsed = JSON.parse(payloadJson) as CardioPayload;
    if (!parsed || typeof parsed !== 'object' || typeof parsed.state !== 'object') return null;
    if (!parsed.context || typeof parsed.context !== 'object') {
      return { ...parsed, context: { source: 'USER' } };
    }
    return parsed;
  } catch {
    return null;
  }
}

export function CaseInput({
  scenarios,
  selectedScenarioId,
  payloadJson,
  statusMessage: _statusMessage,
  onScenarioChange,
  onPayloadChange,
  onRunEvaluation,
  onReset,
  isLoading,
}: CaseInputProps) {
  const [showPayload, setShowPayload] = useState(false);

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? scenarios[0],
    [scenarios, selectedScenarioId]
  );

  const parsedPayload = useMemo(() => parsePayload(payloadJson), [payloadJson]);

  function updatePayload(nextPayload: CardioPayload) {
    onPayloadChange(JSON.stringify(nextPayload, null, 2));
  }

  function updateStateField(field: string, value: unknown) {
    if (!parsedPayload) return;
    const newState = { ...parsedPayload.state };

    if (value === '' || value === null) {
      delete newState[field];
    } else {
      newState[field] = value;
    }

    updatePayload({
      ...parsedPayload,
      state: newState,
    });
  }

  function updateContextField(field: string, value: string) {
    if (!parsedPayload) return;
    const newContext = { ...parsedPayload.context };

    if (value === '' || value === null) {
      delete newContext[field];
    } else {
      newContext[field] = value;
    }

    updatePayload({
      ...parsedPayload,
      context: newContext,
    });
  }

  const state = parsedPayload?.state ?? {};

  return (
    <div className="flex h-full flex-col bg-card/30">
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-sm font-medium text-muted-foreground">Case Intake</h2>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-5">
        <IntakeSection label="Scenario">
          <div className="flex flex-wrap gap-1.5">
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => onScenarioChange(scenario.id)}
                className={cn(
                  'h-8 rounded-sm px-3 text-xs font-medium transition-colors',
                  selectedScenarioId === scenario.id
                    ? 'border border-accent bg-accent text-accent-foreground shadow-sm'
                    : scenarioToneById[scenario.id].idle
                )}
              >
                {scenario.label}
              </button>
            ))}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground/70">
            Scenario selection preloads input and auto-runs evaluation. Run Evaluation remains available for manual reruns.
          </p>
        </IntakeSection>

        <IntakeSection label="Presenting Complaint">
          <div className="grid grid-cols-1 gap-2">
            <NumberField
              label="Age (years)"
              value={asNumber(state.age)}
              onChange={(value) => updateStateField('age', value)}
            />
            <ToggleField
              label="Chest pain present"
              checked={Boolean(state.chest_pain_present)}
              onChange={(checked) => updateStateField('chest_pain_present', checked)}
            />
            <SelectField
              label="Pain character"
              value={asString(state.pain_character)}
              options={[
                { label: 'None / Unknown', value: '' },
                { label: 'Pressure', value: 'pressure' },
                { label: 'Sharp', value: 'sharp' },
                { label: 'Tearing', value: 'tearing' },
                { label: 'Burning', value: 'burning' },
                { label: 'Aching', value: 'aching' },
              ]}
              onChange={(value) => updateStateField('pain_character', value)}
            />
            <div className="grid grid-cols-2 gap-2">
              <NumberField
                label="Pain duration (min)"
                value={asNumber(state.pain_duration_minutes)}
                onChange={(value) => updateStateField('pain_duration_minutes', value)}
              />
              <SelectField
                label="Pain severity"
                value={asString(state.pain_severity)}
                options={[
                  { label: 'None / Unknown', value: '' },
                  { label: 'Mild', value: 'mild' },
                  { label: 'Moderate', value: 'moderate' },
                  { label: 'Severe', value: 'severe' },
                ]}
                onChange={(value) => updateStateField('pain_severity', value)}
              />
            </div>
            <SelectField
              label="Pain radiation"
              value={asString(state.pain_radiation)}
              options={[
                { label: 'None / Unknown', value: '' },
                { label: 'Left arm', value: 'left_arm' },
                { label: 'Jaw', value: 'jaw' },
                { label: 'Back', value: 'back' },
                { label: 'Right arm', value: 'right_arm' },
                { label: 'Both arms', value: 'both_arms' },
              ]}
              onChange={(value) => updateStateField('pain_radiation', value)}
            />
          </div>
        </IntakeSection>

        <IntakeSection label="Associated Symptoms">
          <div className="grid grid-cols-1 gap-2">
            <ToggleField label="Dyspnea" checked={Boolean(state.dyspnea)} onChange={(checked) => updateStateField('dyspnea', checked)} />
            <ToggleField label="Syncope" checked={Boolean(state.syncope)} onChange={(checked) => updateStateField('syncope', checked)} />
            <ToggleField
              label="Diaphoresis"
              checked={Boolean(state.diaphoresis)}
              onChange={(checked) => updateStateField('diaphoresis', checked)}
            />
          </div>
        </IntakeSection>

        <IntakeSection label="Vitals">
          <div className="grid grid-cols-2 gap-2">
            <NumberField
              label="Systolic BP"
              value={asNumber(state.systolic_bp)}
              onChange={(value) => updateStateField('systolic_bp', value)}
            />
            <NumberField
              label="Heart rate"
              value={asNumber(state.heart_rate)}
              onChange={(value) => updateStateField('heart_rate', value)}
            />
          </div>
        </IntakeSection>

        <IntakeSection label="Cardiovascular History">
          <div className="grid grid-cols-1 gap-2">
            <ToggleField
              label="Known CAD"
              checked={Boolean(state.known_cad)}
              onChange={(checked) => updateStateField('known_cad', checked)}
            />
            <ToggleField
              label="Exertional chest pain"
              checked={Boolean(state.exertional_chest_pain)}
              onChange={(checked) => updateStateField('exertional_chest_pain', checked)}
            />
            <NumberField
              label="CV risk factors count"
              value={asNumber(state.cv_risk_factors_count)}
              onChange={(value) => updateStateField('cv_risk_factors_count', value)}
            />
          </div>
        </IntakeSection>

        <IntakeSection label="Medications / Context">
          <div className="grid grid-cols-1 gap-2">
            <ToggleField
              label="No current meds"
              checked={Boolean(state.current_meds_none)}
              onChange={(checked) => updateStateField('current_meds_none', checked)}
            />
            <TextField
              label="Context source"
              value={parsedPayload?.context?.source ?? 'USER'}
              onChange={(value) => updateContextField('source', value || 'USER')}
            />
          </div>
        </IntakeSection>

        <IntakeSection label="Status">
          <div className="rounded-md border border-border/70 bg-secondary/50 px-3 py-2">
            <div className="flex items-center gap-2 text-[11px] text-foreground/85">
              {!isLoading && <span className="h-1.5 w-1.5 rounded-full bg-emerald-500/80" />}
              <span>Deterministic evaluation ready.</span>
            </div>
          </div>
          {isLoading && (
            <div className="mt-2 inline-flex items-center gap-1.5 rounded-sm border border-accent/30 bg-accent/10 px-2 py-1 text-[10px] uppercase tracking-wider text-accent">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
              Running evaluation
            </div>
          )}
        </IntakeSection>

        <div className="border-t border-border/50 pt-4">
          <button
            onClick={() => setShowPayload(!showPayload)}
            className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50 transition-colors hover:text-muted-foreground"
          >
            <span className={cn('transition-transform', showPayload && 'rotate-90')}>{'▸'}</span>
            Technical JSON Preview
          </button>
          {showPayload && (
            <textarea
              className="mt-2 min-h-56 w-full resize-y rounded-md bg-background/50 p-3 font-mono text-[10px] text-muted-foreground/90 outline-none ring-1 ring-border focus:ring-2"
              spellCheck={false}
              value={payloadJson}
              onChange={(event) => onPayloadChange(event.target.value)}
            />
          )}
          {!parsedPayload && (
            <p className="mt-2 text-[10px] text-status-urgent/80">JSON is invalid; structured form editing is temporarily unavailable.</p>
          )}
        </div>
      </div>

      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <button
            onClick={onRunEvaluation}
            disabled={isLoading}
            className={cn(
              'flex-1 rounded-sm bg-accent px-4 py-2 text-xs font-semibold text-accent-foreground transition-colors',
              isLoading ? 'cursor-not-allowed opacity-50' : 'hover:bg-accent/90'
            )}
          >
            {isLoading ? 'Evaluating...' : 'Run Evaluation'}
          </button>
          <button
            onClick={onReset}
            disabled={isLoading}
            className="rounded-sm px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary/50"
          >
            Reset
          </button>
        </div>
        <div className="mt-3 border-t border-border/60 py-3 text-center text-[10px] text-muted-foreground/60">
          Routing is deterministic and policy-governed. Generative AI is not used for final clinical decisions.
        </div>
      </div>
    </div>
  );
}

function IntakeSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h3 className="mb-2 text-sm font-medium text-muted-foreground">{label}</h3>
      <div className="rounded-lg border border-border/60 bg-card p-4 shadow-sm">{children}</div>
    </section>
  );
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function asNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function NumberField({ label, value, onChange }: { label: string; value: number | null; onChange: (value: number | null) => void }) {
  return (
    <label className="space-y-1">
      <span className="text-[10px] text-muted-foreground/70">{label}</span>
      <input
        type="number"
        className="h-9 w-full rounded-sm bg-background px-2 py-1.5 text-xs text-foreground outline-none ring-1 ring-border transition-colors hover:border-accent/50 focus:border-accent focus:ring-2"
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value === '' ? null : Number(event.target.value))}
      />
    </label>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-1">
      <span className="text-[10px] text-muted-foreground/70">{label}</span>
      <input
        type="text"
        className="h-9 w-full rounded-sm bg-background px-2 py-1.5 text-xs text-foreground outline-none ring-1 ring-border transition-colors hover:border-accent/50 focus:border-accent focus:ring-2"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<{ label: string; value: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-1">
      <span className="text-[10px] text-muted-foreground/70">{label}</span>
      <select
        className="h-9 w-full rounded-sm bg-background px-2 py-1.5 text-xs text-foreground outline-none ring-1 ring-border transition-colors hover:border-accent/50 focus:border-accent focus:ring-2"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={`${label}-${option.value || 'empty'}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ToggleField({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="inline-flex h-9 items-center justify-between rounded-sm border border-border bg-background px-2.5 py-2 text-xs text-foreground/90 transition-colors hover:border-accent/50 has-[:checked]:border-accent/30 has-[:checked]:bg-accent/5">
      <span>{label}</span>
      <input
        type="checkbox"
        className="h-3.5 w-3.5 accent-[var(--accent)]"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  );
}
