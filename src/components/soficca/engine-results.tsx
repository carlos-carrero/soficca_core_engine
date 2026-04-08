'use client';

import { useState } from 'react';

import type { CardioReport } from '@/lib/cardio-types';
import { cn } from '@/lib/utils';

type EngineResultsProps = {
  result: CardioReport | null;
  isLoading: boolean;
};

export function EngineResults({ result, isLoading }: EngineResultsProps) {
  if (isLoading) return <LoadingState />;
  if (!result) return <EmptyState />;
  const statusTone = getStatusToneClasses(result.decision.status);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-accent" />
          <h2 className="text-xs font-medium uppercase tracking-widest text-muted-foreground">Governed Decision Output</h2>
          <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-medium', statusTone.pill)}>
            {result.decision.status}
          </span>
        </div>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-6">
        {result.safety.status === 'TRIGGERED' && <SafetyOverrideBanner report={result} />}
        <CaseSummaryBlock report={result} />
        <DecisionCard report={result} />
        <SafetyStatusCard report={result} />
        <OperationalNextStepsCard report={result} />
        <TechnicalTraceCard report={result} />
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Governed Decision Output</h2>
      </div>
      <div className="flex flex-1 items-center justify-center">
        <div className="space-y-4 text-center">
          <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-border border-t-foreground" />
          <p className="text-xs text-muted-foreground">Processing evaluation...</p>
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Governed Decision Output</h2>
      </div>
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="max-w-xs space-y-4 text-center">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-secondary/50">
            <span className="text-lg text-muted-foreground">⎈</span>
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">
            Select a scenario and run evaluation to generate deterministic routing output.
          </p>
        </div>
      </div>
    </div>
  );
}

function SafetyOverrideBanner({ report }: { report: CardioReport }) {
  return (
    <section className="rounded-lg border border-status-emergency/40 bg-status-emergency/10 p-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-status-emergency">Safety Override Active</h3>
        <span className="rounded-sm bg-status-emergency/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-status-emergency">
          {report.safety.action}
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {report.safety.triggers.map((trigger) => (
          <span key={trigger} className="rounded-sm border border-status-emergency/35 bg-status-emergency/15 px-2 py-1 text-[11px] font-mono text-status-emergency">
            {trigger}
          </span>
        ))}
      </div>
    </section>
  );
}

function CaseSummaryBlock({ report }: { report: CardioReport }) {
  const tone = getStatusToneClasses(report.decision.status);
  const routeLabel = translateRoutePath(report.trace.final_route);
  const investorSummary =
    report.decision.status === 'CONFLICT'
      ? 'Input conflict detected. The engine paused routing to avoid an unsafe classification.'
      : report.decision.status === 'NEEDS_MORE_INFO'
        ? 'Required clinical inputs are incomplete. The engine withheld routing until critical fields are confirmed.'
        : report.decision.clinical_summary;

  return (
    <div className={cn('rounded-md border border-border/50 border-l-[3px] bg-secondary/30 px-4 py-4', tone.border)}>
      <div className="mb-3 rounded-md border border-border/60 bg-background/70 px-3 py-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Decision Contract</p>
        <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
          <span>
            Engine: <span className="font-mono">{report.versions.engine}</span>
          </span>
          <span>
            Contract: <span className="font-mono">{report.versions.contract}</span>
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-medium', tone.pill)}>{report.decision.status}</span>
      </div>
      <p className="mt-3 text-base font-semibold leading-relaxed text-foreground">{routeLabel}</p>
      <p className="mt-2 text-[15px] font-medium leading-relaxed text-foreground/90">{investorSummary}</p>
    </div>
  );
}

function DecisionCard({ report }: { report: CardioReport }) {
  const tone = getStatusToneClasses(report.decision.status);
  return (
    <section className={cn('rounded-lg border border-border border-l-[3px] bg-card p-6', tone.border)}>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Clinical Route</h3>
      {renderDecisionByStatus(report)}
    </section>
  );
}

function renderDecisionByStatus(report: CardioReport) {
  switch (report.decision.status) {
    case 'DECIDED':
      return (
        <div className="space-y-3">
          <p className="text-sm text-foreground/90">{report.decision.clinical_summary}</p>
          <WhyRouteChosenList
            facts={[
              `Final clinical route: ${translateRoutePath(report.trace.final_route)}`,
              report.decision.reasons[0] ?? 'No high-risk contradiction was detected in structured inputs.',
              report.trace.rules_triggered[0] ?? 'Deterministic rules completed without safety override.',
            ]}
          />
        </div>
      );

    case 'NEEDS_MORE_INFO':
      return (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Decision withheld for safety pending completion of required clinical inputs.</p>
          <WhyRouteChosenList
            facts={[
              'Decision withheld for safety.',
              `${report.decision.missing_fields.length} critical field(s) still require confirmation.`,
              'Routing resumes automatically once missing fields are completed.',
            ]}
          />
        </div>
      );

    case 'CONFLICT':
      return (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Conflicting structured inputs detected; routing deferred for clinician review.</p>
          <WhyRouteChosenList
            facts={[
              'Routing halted because contradictory inputs were detected.',
              report.trace.conflicts_detected[0]
                ? translateConflict(report.trace.conflicts_detected[0])
                : 'Contradictory clinical inputs detected requiring manual review',
              'Manual verification is required before deterministic routing can continue.',
            ]}
          />
        </div>
      );

    case 'ESCALATED':
      return (
        <div className="space-y-3">
          <div className="rounded-md border border-status-emergency/25 bg-status-emergency/[0.06] px-3 py-2 text-xs text-status-emergency">
            Urgency: <span className="font-mono">{report.decision.urgency_level}</span>
          </div>
          <p className="text-sm text-foreground/90">{report.decision.clinical_summary}</p>
          <WhyRouteChosenList
            facts={[
              report.decision.reasons[0] ?? 'Risk signals met escalation criteria.',
              report.trace.rules_triggered[0] ?? 'Safety and decision rules aligned on immediate escalation.',
              `Final clinical route: ${translateRoutePath(report.trace.final_route)}`,
            ]}
          />
        </div>
      );

    default: {
      const unreachable: never = report.decision.status;
      return unreachable;
    }
  }
}

function SafetyStatusCard({ report }: { report: CardioReport }) {
  const tone = getStatusToneClasses(report.decision.status);
  return (
    <section
      className={cn(
        'rounded-lg border border-l-[3px] p-5',
        tone.border,
        report.safety.status === 'TRIGGERED' ? 'border-status-emergency/15 bg-status-emergency/[0.03]' : 'border-border bg-card'
      )}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Safety Verification</h3>
      </div>

      {report.safety.action === 'NONE' ? (
        <div className="mb-3 space-y-1">
          <p className="text-sm font-medium text-foreground/90">Safety status: Clear</p>
          <p className="text-xs text-muted-foreground">No emergency red flags detected. Required fields complete.</p>
        </div>
      ) : (
        <div className="mb-3 rounded-md border border-status-emergency/35 bg-status-emergency/10 px-3 py-2 text-xs text-status-emergency">
          Safety policy overrode baseline route due to risk triggers.
        </div>
      )}

      <div className="space-y-2">
        <ChipRow items={report.safety.triggers.length ? report.safety.triggers : ['No active safety triggers']} tone="secondary" />
        {report.safety.flags.length > 0 && <ChipRow items={report.safety.flags} tone="danger" />}
      </div>
    </section>
  );
}

function OperationalNextStepsCard({ report }: { report: CardioReport }) {
  const tone = getStatusToneClasses(report.decision.status);
  const intakeActions = [
    ...report.decision.missing_fields.map((field) => translateMissingField(field)),
    ...report.trace.conflicts_detected.map((conflict) => translateConflict(conflict)),
  ];
  const hasContent =
    report.decision.required_actions.length > 0 || intakeActions.length > 0;

  return (
    <section className={cn('rounded-lg border border-border border-l-[3px] bg-card p-5', tone.border)}>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Action Plan</h3>
      {!hasContent ? (
        <p className="text-xs italic text-muted-foreground">No operational steps required.</p>
      ) : (
        <div className="space-y-4">
          {report.decision.required_actions.length > 0 && (
            <ListSection
              title="Recommended Clinical Action"
              colorClass="text-accent"
              bulletClass="bg-accent/60"
              items={report.decision.required_actions}
            />
          )}
          {intakeActions.length > 0 && <ChipSection title="Required Intake Action" tone="warning" items={intakeActions} />
          }
        </div>
      )}
    </section>
  );
}

function WhyRouteChosenList({ facts }: { facts: string[] }) {
  return (
    <div className="space-y-2 rounded-md border border-border/70 bg-background/25 px-3 py-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Why this route was chosen</p>
      <ul className="space-y-1.5">
        {facts.slice(0, 3).map((fact, index) => (
          <li key={`${fact}-${index}`} className="flex items-start gap-2 text-xs text-foreground/85">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent/80" />
            {fact}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ListSection({ title, items, colorClass, bulletClass }: { title: string; items: string[]; colorClass: string; bulletClass: string }) {
  return (
    <div className="space-y-2">
      <span className={cn('text-[10px] font-medium uppercase tracking-wider', colorClass)}>{title}</span>
      <ul className="space-y-1">
        {items.map((item, index) => (
          <li key={`${title}-${item}-${index}`} className="flex items-start gap-2 text-xs text-foreground/80">
            <span className={cn('mt-1.5 h-1 w-1 shrink-0 rounded-full', bulletClass)} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChipSection({ title, items, tone }: { title: string; items: string[]; tone: 'warning' | 'info' }) {
  return (
    <div className="space-y-2">
      <span className={cn('text-[10px] font-medium uppercase tracking-wider', tone === 'warning' ? 'text-status-urgent' : 'text-status-info')}>
        {title}
      </span>
      <ChipRow items={items} tone={tone} />
    </div>
  );
}

function ChipRow({ items, tone }: { items: string[]; tone: 'secondary' | 'warning' | 'info' | 'danger' }) {
  const toneClass: Record<typeof tone, string> = {
    secondary: 'bg-secondary/60 text-foreground/85',
    warning: 'bg-status-urgent/15 text-status-urgent border border-status-urgent/25',
    info: 'bg-status-info/15 text-status-info border border-status-info/25',
    danger: 'bg-status-emergency/15 text-status-emergency border border-status-emergency/25',
  };

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, index) => (
        <span key={`${item}-${index}`} className={cn('rounded-sm px-2 py-1 text-[11px] font-mono', toneClass[tone])}>
          {item}
        </span>
      ))}
    </div>
  );
}

function TechnicalTraceCard({ report }: { report: CardioReport }) {
  const [isJsonExpanded, setIsJsonExpanded] = useState(false);
  const tone = getStatusToneClasses(report.decision.status);
  const preliminaryRoute = translateRoutePath(report.trace.preliminary_route);
  const finalRoute = translateRoutePath(report.trace.final_route);
  const hasOverride = report.trace.preliminary_route !== report.trace.final_route;
  const routeLabel = `Preliminary route: ${preliminaryRoute} → Final route: ${finalRoute}`;

  return (
    <section className={cn('rounded-lg border border-border border-l-[3px] bg-card p-5', tone.border)}>
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Trace</h3>

      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-border/70 bg-secondary/40 px-2.5 py-1 text-[11px] text-muted-foreground">
            Route: <span className="text-foreground/80">{routeLabel}</span>
          </span>
          {!hasOverride && (
            <span className="rounded-full border border-border/70 bg-secondary/40 px-2.5 py-1 text-[11px] text-muted-foreground">
              No override applied
            </span>
          )}
          <span className="rounded-full border border-border/70 bg-secondary/40 px-2.5 py-1 text-[11px] text-muted-foreground">
            Rules triggered: <span className="font-mono text-foreground/80">{report.trace.rules_triggered.length}</span>
          </span>
          <span className="rounded-full border border-border/70 bg-secondary/40 px-2.5 py-1 text-[11px] text-muted-foreground">
            Policies triggered: <span className="font-mono text-foreground/80">{report.trace.policy_trace.triggered.length}</span>
          </span>
        </div>

        <div className="pt-1">
          <button
            onClick={() => setIsJsonExpanded(!isJsonExpanded)}
            className="flex items-center gap-1.5 text-[10px] font-medium text-muted-foreground/60 underline-offset-4 transition-colors hover:text-muted-foreground hover:underline"
          >
            <span className={cn('transition-transform', isJsonExpanded && 'rotate-90')}>{'▸'}</span>
            Technical Contract View
          </button>
          {isJsonExpanded && (
            <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-background/50 p-3 font-mono text-[10px] text-muted-foreground/70">
              {JSON.stringify(report.trace, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </section>
  );
}

function getStatusToneClasses(status: CardioReport['decision']['status']) {
  switch (status) {
    case 'DECIDED':
      return {
        border: 'border-l-emerald-500/80',
        pill: 'border-emerald-500/30 bg-emerald-500/15 text-emerald-300',
      };
    case 'NEEDS_MORE_INFO':
      return {
        border: 'border-l-sky-500/80',
        pill: 'border-sky-500/30 bg-sky-500/15 text-sky-300',
      };
    case 'CONFLICT':
      return {
        border: 'border-l-amber-500/80',
        pill: 'border-amber-500/30 bg-amber-500/15 text-amber-300',
      };
    case 'ESCALATED':
      return {
        border: 'border-l-red-500/80',
        pill: 'border-red-500/30 bg-red-500/15 text-red-300',
      };
  }
}

function translateRoutePath(path: string | null): string {
  switch (path) {
    case 'PATH_ROUTINE':
      return 'Routine Review';
    case 'PATH_URGENT_SAME_DAY':
      return 'Same-Day Urgent Review';
    case 'PATH_EMERGENCY_NOW':
      return 'Emergency Escalation';
    default:
      return 'Safe Routing Deferred';
  }
}

function translateMissingField(field: string): string {
  switch (field) {
    case 'pain_duration_minutes':
      return 'Confirm chest pain duration';
    case 'pain_character':
      return 'Confirm chest pain character';
    case 'pain_radiation':
      return 'Confirm radiation';
    case 'prior_mi_or_known_cad':
      return 'Confirm prior MI / known CAD';
    default:
      return field
        .split('_')
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
  }
}

function translateConflict(conflict: string): string {
  switch (conflict) {
    case 'CONFLICT_PAIN_SEVERITY_WITHOUT_CHEST_PAIN':
      return 'Pain severity was provided while chest pain is marked absent';
    case 'CONFLICT_RADIATION_WITHOUT_CHEST_PAIN':
      return 'Radiation was provided while chest pain is marked absent';
    case 'CONFLICT_PAIN_CHARACTER_WITHOUT_CHEST_PAIN':
      return 'Pain character was provided while chest pain is marked absent';
    case 'CONFLICT_PAIN_DURATION_WITHOUT_CHEST_PAIN':
      return 'Pain duration was provided while chest pain is marked absent';
    case 'CONFLICT_EXERTIONAL_WITHOUT_CHEST_PAIN':
      return 'Exertional history was provided while chest pain is marked absent';
    default:
      return 'Contradictory clinical inputs detected requiring manual review';
  }
}
