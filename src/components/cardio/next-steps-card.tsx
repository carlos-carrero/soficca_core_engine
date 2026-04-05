import type { CardioReport } from '@/lib/cardio-types';

type NextStepsCardProps = {
  report: CardioReport;
};

export function NextStepsCard({ report }: NextStepsCardProps) {
  return (
    <section className="rounded-2xl border border-slate-700/60 bg-panel/70 p-5">
      <h3 className="text-lg font-semibold text-slate-100">Recommended Next Steps</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div>
          <p className="mb-1 text-xs uppercase tracking-wide text-slate-400">Required actions</p>
          <ul className="space-y-1 text-sm text-slate-200">
            {report.decision.required_actions.map((action) => (
              <li key={action} className="rounded-md bg-slate-950/50 px-2 py-1">
                {action}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 text-xs uppercase tracking-wide text-slate-400">Missing fields</p>
          <ul className="space-y-1 text-sm text-slate-200">
            {(report.decision.missing_fields.length ? report.decision.missing_fields : ['None']).map((field) => (
              <li key={field} className="rounded-md bg-slate-950/50 px-2 py-1">
                {field}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
