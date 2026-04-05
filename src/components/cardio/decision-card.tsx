import type { CardioReport } from '@/lib/cardio-types';
import { decisionHeadline, decisionTone } from '@/lib/cardio-view-model';

type DecisionCardProps = {
  report: CardioReport;
};

export function DecisionCard({ report }: DecisionCardProps) {
  return (
    <section className="rounded-2xl border border-slate-600/70 bg-gradient-to-br from-slate-900/95 to-slate-800/70 p-6 shadow-panel">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Clinical Routing Decision</p>
      <h2 className="mt-2 font-[var(--font-space-grotesk)] text-3xl font-semibold text-slate-100">{decisionHeadline(report)}</h2>
      <p className="mt-3 text-sm text-slate-300">{report.decision.clinical_summary}</p>

      <div className="mt-5 grid gap-2 text-sm sm:grid-cols-3">
        <div className="rounded-lg border border-slate-700 bg-slate-950/55 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-400">Decision Type</p>
          <p className={`mt-1 font-medium ${decisionTone(report.decision.status)}`}>{report.decision.decision_type}</p>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-950/55 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-400">Final Route</p>
          <p className="mt-1 font-medium text-slate-100">{report.trace.final_route ?? '—'}</p>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-950/55 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-400">Urgency</p>
          <p className="mt-1 font-medium text-slate-100">{report.decision.urgency_level}</p>
        </div>
      </div>
    </section>
  );
}
