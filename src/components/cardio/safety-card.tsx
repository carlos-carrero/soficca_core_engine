import type { CardioReport } from '@/lib/cardio-types';
import { safetyLabel } from '@/lib/cardio-view-model';

type SafetyCardProps = {
  report: CardioReport;
};

export function SafetyCard({ report }: SafetyCardProps) {
  const isTriggered = report.safety.status === 'TRIGGERED';

  return (
    <section className={`rounded-2xl border p-5 ${isTriggered ? 'border-danger/70 bg-danger/10' : 'border-slate-700/60 bg-panel/70'}`}>
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Safety</p>
      <h3 className="mt-2 text-lg font-semibold text-slate-100">{safetyLabel(report)}</h3>
      <p className="mt-2 text-sm text-slate-300">Action: {report.safety.action}</p>
      <ul className="mt-3 space-y-1 text-sm text-slate-200">
        {(report.safety.triggers.length ? report.safety.triggers : ['No active safety triggers']).map((trigger) => (
          <li key={trigger} className="rounded-md bg-slate-950/40 px-2 py-1">
            {trigger}
          </li>
        ))}
      </ul>
    </section>
  );
}
