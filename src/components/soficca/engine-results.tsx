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

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Engine Output</h2>
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
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Engine Output</h2>
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
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Engine Output</h2>
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
  return (
    <div className="rounded-md border border-border/50 bg-secondary/30 px-4 py-3">
      <div className="flex items-start gap-3">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Case</span>
        <p className="flex-1 text-sm leading-relaxed text-foreground/90">{report.decision.clinical_summary}</p>
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-muted-foreground/80">
        <span>Engine: <span className="font-mono">{report.versions.engine}</span></span>
        <span>Contract: <span className="font-mono">{report.versions.contract}</span></span>
      </div>
    </div>
  );
}

function DecisionCard({ report }: { report: CardioReport }) {
  return (
    <section className="rounded-lg border border-border bg-card p-6">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Decision</h3>
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
          <div className="rounded-md border border-border/70 bg-background/25 px-3 py-2 text-xs text-muted-foreground">
            Path: <span className="font-mono text-foreground/85">{report.decision.path ?? '—'}</span>
          </div>
        </div>
      );

    case 'NEEDS_MORE_INFO':
      return (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Missing data blocks safe routing. Collect these fields:</p>
          <ul className="space-y-1">
            {(report.decision.missing_fields.length ? report.decision.missing_fields : ['None']).map((field) => (
              <li key={field} className="rounded-sm bg-secondary/70 px-2 py-1 text-xs font-mono text-foreground/85">
                {field}
              </li>
            ))}
          </ul>
        </div>
      );

    case 'CONFLICT':
      return (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Conflicting structured inputs detected; routing deferred.</p>
          <div className="flex flex-wrap gap-1.5">
            {(report.trace.conflicts_detected.length ? report.trace.conflicts_detected : ['No conflict IDs']).map((item) => (
              <span key={item} className="rounded-sm border border-status-info/25 bg-status-info/10 px-2 py-1 text-[11px] font-mono text-status-info">
                {item}
              </span>
            ))}
          </div>
        </div>
      );

    case 'ESCALATED':
      return (
        <div className="space-y-3">
          <div className="rounded-md border border-status-emergency/25 bg-status-emergency/[0.06] px-3 py-2 text-xs text-status-emergency">
            Urgency: <span className="font-mono">{report.decision.urgency_level}</span>
          </div>
          <p className="text-sm text-foreground/90">{report.decision.clinical_summary}</p>
          <ul className="space-y-1">
            {(report.decision.reasons.length ? report.decision.reasons : ['No explicit reasons']).map((reason, index) => (
              <li key={`${reason}-${index}`} className="rounded-sm bg-secondary/70 px-2 py-1 text-xs text-foreground/85">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      );

    default: {
      const unreachable: never = report.decision.status;
      return unreachable;
    }
  }
}

function SafetyStatusCard({ report }: { report: CardioReport }) {
  return (
    <section className={cn('rounded-lg border p-5', report.safety.status === 'TRIGGERED' ? 'border-status-emergency/15 bg-status-emergency/[0.03]' : 'border-border bg-card')}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Safety Layer</h3>
      </div>

      <p className="mb-3 text-xs text-muted-foreground">
        Action: <span className="font-mono text-foreground/80">{report.safety.action}</span>
      </p>

      <div className="space-y-2">
        <ChipRow items={report.safety.triggers.length ? report.safety.triggers : ['No active safety triggers']} tone="secondary" />
        {report.safety.flags.length > 0 && <ChipRow items={report.safety.flags} tone="danger" />}
      </div>
    </section>
  );
}

function OperationalNextStepsCard({ report }: { report: CardioReport }) {
  const hasContent =
    report.decision.required_actions.length > 0 || report.decision.missing_fields.length > 0 || report.trace.conflicts_detected.length > 0;

  return (
    <section className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Next Steps</h3>
      {!hasContent ? (
        <p className="text-xs italic text-muted-foreground">No operational steps required.</p>
      ) : (
        <div className="space-y-4">
          {report.decision.required_actions.length > 0 && (
            <ListSection title="Recommended Actions" colorClass="text-accent" bulletClass="bg-accent/60" items={report.decision.required_actions} />
          )}
          {report.decision.missing_fields.length > 0 && (
            <ChipSection title="Missing Data" tone="warning" items={report.decision.missing_fields} />
          )}
          {report.trace.conflicts_detected.length > 0 && <ChipSection title="Conflicts" tone="info" items={report.trace.conflicts_detected} />}
        </div>
      )}
    </section>
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

  return (
    <section className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Trace</h3>

      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground/70">
          <span>
            Route: <span className="font-mono text-foreground/70">{report.trace.preliminary_route ?? '—'}</span>
            {report.trace.preliminary_route && report.trace.preliminary_route !== report.trace.final_route && (
              <>
                <span className="mx-1.5 text-muted-foreground/40">→</span>
                <span className="font-mono text-foreground/70">{report.trace.final_route ?? '—'}</span>
              </>
            )}
          </span>
          <span className="text-muted-foreground/40">|</span>
          <span>Rules triggered: <span className="font-mono text-foreground/70">{report.trace.rules_triggered.length}</span></span>
          <span className="text-muted-foreground/40">|</span>
          <span>Policies triggered: <span className="font-mono text-foreground/70">{report.trace.policy_trace.triggered.length}</span></span>
        </div>

        <div className="pt-1">
          <button
            onClick={() => setIsJsonExpanded(!isJsonExpanded)}
            className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50 transition-colors hover:text-muted-foreground"
          >
            <span className={cn('transition-transform', isJsonExpanded && 'rotate-90')}>{'▸'}</span>
            Raw Trace JSON
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
