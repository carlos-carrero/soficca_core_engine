'use client';

import { useEffect, useState } from 'react';

import type { EngineViewModel, UiUrgency } from '@/lib/cardio-ui-adapter';
import { cn } from '@/lib/utils';

type EngineResultsProps = {
  result: EngineViewModel | null;
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
        <CaseSummaryBlock summary={result.caseSummary} />
        <DecisionSummaryCard summary={result.decisionSummary} />
        <SafetyStatusCard status={result.safetyStatus} />
        <OperationalNextStepsCard steps={result.operationalNextSteps} />
        <TechnicalTraceCard trace={result.technicalTrace} />
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

function CaseSummaryBlock({ summary }: { summary: string }) {
  return (
    <div className="rounded-md border border-border/50 bg-secondary/30 px-4 py-3">
      <div className="flex items-start gap-3">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Case</span>
        <p className="flex-1 text-sm leading-relaxed text-foreground/90">{summary}</p>
      </div>
    </div>
  );
}

function DecisionSummaryCard({ summary }: { summary: EngineViewModel['decisionSummary'] }) {
  const isEmergency = summary.decisionType === 'EMERGENCY_OVERRIDE';

  return (
    <section className={cn('rounded-lg border p-6', isEmergency ? 'border-status-emergency/20 bg-status-emergency/5' : 'border-border bg-card')}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex-1 space-y-1">
          <h3 className="text-xl font-semibold tracking-tight text-foreground">{summary.title}</h3>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <UrgencyBadge urgency={summary.urgency} />
        <RouteBadge route={summary.finalRoute} />
      </div>

      <RouteProgression summary={summary} />

      <div className="mb-5 flex flex-wrap gap-3 text-[11px] text-muted-foreground">
        <span>
          Status: <span className="font-mono text-foreground/80">{summary.status}</span>
        </span>
        <span>
          Type: <span className="font-mono text-foreground/80">{summary.decisionType}</span>
        </span>
        <span>
          Recommended: <span className="font-mono text-foreground/80">{summary.recommendedRoute ?? '—'}</span>
        </span>
      </div>

      <p className="text-sm leading-relaxed text-muted-foreground">{summary.rationale}</p>
    </section>
  );
}

function RouteProgression({ summary }: { summary: EngineViewModel['decisionSummary'] }) {
  const preliminary = summary.preliminaryRoute ?? '—';
  const finalRoute = summary.finalRoute ?? '—';
  const changed = summary.preliminaryRoute && summary.preliminaryRoute !== summary.finalRoute;

  return (
    <div
      className={cn(
        'mb-4 rounded-md border px-3 py-2',
        changed ? 'border-status-urgent/20 bg-status-urgent/[0.06]' : 'border-border/70 bg-background/25'
      )}
    >
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-muted-foreground/80">
        <span>Route Progression</span>
        {changed && <span className="rounded-sm bg-status-urgent/20 px-1.5 py-0.5 text-status-urgent">Refined</span>}
      </div>
      <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-[11px] text-foreground/85">{preliminary}</span>
        <span className={cn('text-muted-foreground/50', changed && 'text-status-urgent/70')}>→</span>
        <span
          className={cn(
            'rounded px-1.5 py-0.5 font-mono text-[11px]',
            changed ? 'bg-status-urgent/20 text-status-urgent' : 'bg-secondary/80 text-foreground/85'
          )}
        >
          {finalRoute}
        </span>
      </div>
    </div>
  );
}

function SafetyStatusCard({ status }: { status: EngineViewModel['safetyStatus'] }) {
  const hasRedFlags = status.redFlagsDetected.length > 0;

  return (
    <section className={cn('rounded-lg border p-5', status.overrideTriggered ? 'border-status-emergency/15 bg-status-emergency/[0.03]' : 'border-border bg-card')}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Safety Layer</h3>
        {status.overrideTriggered && (
          <span className="rounded-sm bg-status-emergency/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-status-emergency">
            Override Active
          </span>
        )}
      </div>

      <p className="mb-3 text-xs text-muted-foreground">
        Action: <span className="font-mono text-foreground/80">{status.action}</span>
      </p>

      {hasRedFlags ? (
        <div className="space-y-3">
          <ChipRow items={status.redFlagsDetected} tone="secondary" />
          {status.flags.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground/70">Safety Flags</span>
              <ChipRow items={status.flags} tone="danger" />
            </div>
          )}
          {status.overrideReason && <p className="text-xs leading-relaxed text-muted-foreground">{status.overrideReason}</p>}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No red flags detected. Safety policy did not require override.</p>
      )}
    </section>
  );
}

function OperationalNextStepsCard({ steps }: { steps: EngineViewModel['operationalNextSteps'] }) {
  const hasContent =
    steps.recommendedActions.length > 0 || steps.missingCriticalInfo.length > 0 || steps.conflictsDetected.length > 0;

  return (
    <section className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Next Steps</h3>
      {!hasContent ? (
        <p className="text-xs italic text-muted-foreground">No operational steps required.</p>
      ) : (
        <div className="space-y-4">
          {steps.recommendedActions.length > 0 && (
            <ListSection title="Recommended Actions" colorClass="text-accent" bulletClass="bg-accent/60" items={steps.recommendedActions} />
          )}
          {steps.missingCriticalInfo.length > 0 && (
            <ChipSection title="Missing Data" tone="warning" items={steps.missingCriticalInfo} />
          )}
          {steps.conflictsDetected.length > 0 && <ChipSection title="Conflicts" tone="info" items={steps.conflictsDetected} />}
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

function TechnicalTraceCard({ trace }: { trace: EngineViewModel['technicalTrace'] }) {
  const [isJsonExpanded, setIsJsonExpanded] = useState(false);
  const [formattedTime, setFormattedTime] = useState<string | null>(null);

  useEffect(() => {
    setFormattedTime(new Date(trace.timestamp).toLocaleTimeString());
  }, [trace.timestamp]);

  return (
    <section className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Trace</h3>

      <div className="space-y-4">
        <div className="space-y-2">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground/70">Triggered IDs</span>
          <div className="flex flex-wrap gap-x-4 gap-y-3">
            <MiniChipGroup title="Rules Activated" items={trace.activatedRules} />
            <MiniChipGroup title="Rules Triggered" items={trace.rulesTriggered} />
            <MiniChipGroup title="Policies Triggered" items={trace.triggeredPolicies} />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="text-muted-foreground/70">
            Route: <span className="font-mono text-foreground/70">{trace.preliminaryRoute ?? '—'}</span>
            {trace.preliminaryRoute && trace.preliminaryRoute !== trace.finalRoute && (
              <>
                <span className="mx-1.5 text-muted-foreground/40">→</span>
                <span className="font-mono text-foreground/70">{trace.finalRoute ?? '—'}</span>
              </>
            )}
          </span>
          <span className="text-muted-foreground/40">|</span>
          <span className="text-muted-foreground/70">
            <span className="font-mono text-foreground/70">{trace.evaluationDurationMs}ms</span>
          </span>
          <span className="text-muted-foreground/40">|</span>
          <span className="text-muted-foreground/70">
            <span className="font-mono text-foreground/70">{formattedTime ?? '—'}</span>
          </span>
        </div>

        {trace.overrideReason && (
          <p className="text-xs text-muted-foreground">
            Override reason: <span className="font-mono text-foreground/80">{trace.overrideReason}</span>
          </p>
        )}

        <div className="pt-1">
          <button
            onClick={() => setIsJsonExpanded(!isJsonExpanded)}
            className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50 transition-colors hover:text-muted-foreground"
          >
            <span className={cn('transition-transform', isJsonExpanded && 'rotate-90')}>{'▸'}</span>
            Raw Trace + Payload
          </button>
          {isJsonExpanded && (
            <pre className="mt-2 max-h-48 overflow-auto rounded-md bg-background/50 p-3 font-mono text-[10px] text-muted-foreground/70">
              {JSON.stringify(trace, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </section>
  );
}

function MiniChipGroup({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;

  return (
    <div className="space-y-1.5">
      <span className="text-[10px] text-muted-foreground/70">{title}</span>
      <div className="flex flex-wrap gap-1">
        {items.map((item, index) => (
          <span
            key={`${title}-${item}-${index}`}
            className="rounded-sm bg-secondary/70 px-1.5 py-0.5 font-mono text-[10px] text-secondary-foreground/80"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function UrgencyBadge({ urgency }: { urgency: UiUrgency }) {
  const styles: Record<UiUrgency, string> = {
    critical: 'bg-status-emergency/15 text-status-emergency',
    high: 'bg-status-urgent/15 text-status-urgent',
    moderate: 'bg-status-info/15 text-status-info',
    low: 'bg-status-routine/15 text-status-routine',
    pending: 'bg-secondary text-muted-foreground',
  };

  return (
    <span className={cn('rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider', styles[urgency])}>
      {urgency}
    </span>
  );
}

function RouteBadge({ route }: { route: string }) {
  return (
    <span className="rounded-sm border border-border px-2 py-0.5 font-mono text-[10px] font-medium text-foreground/90">
      {route}
    </span>
  );
}
