import type { CardioReport } from '@/lib/cardio-types';

type TraceCardProps = {
  report: CardioReport;
};

export function TraceCard({ report }: TraceCardProps) {
  return (
    <section className="rounded-2xl border border-slate-700/60 bg-panel/60 p-5">
      <h3 className="text-base font-semibold text-slate-100">Operational Trace (Secondary)</h3>
      <div className="mt-3 grid gap-3 text-xs text-slate-300 md:grid-cols-2">
        <div>
          <p className="mb-1 uppercase tracking-wide text-slate-400">Activated Rules</p>
          <p>{report.trace.activated_rules.join(', ') || 'None'}</p>
        </div>
        <div>
          <p className="mb-1 uppercase tracking-wide text-slate-400">Policy Triggered</p>
          <p>{report.trace.policy_trace.triggered.join(', ') || 'None'}</p>
        </div>
      </div>
      <pre className="mt-4 max-h-64 overflow-auto rounded-lg border border-slate-700 bg-slate-950/75 p-3 text-xs text-slate-300">
        {JSON.stringify(report.trace, null, 2)}
      </pre>
    </section>
  );
}
