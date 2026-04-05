import type { CardioReport, CardioScenarioId } from '@/lib/cardio-types';

type CaseSummaryProps = {
  report: CardioReport;
  scenarioId: CardioScenarioId;
};

export function CaseSummary({ report, scenarioId }: CaseSummaryProps) {
  return (
    <section className="rounded-2xl border border-slate-700/60 bg-panel/80 p-5">
      <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
        <span className="rounded-full border border-slate-600 px-2 py-1">Scenario · {scenarioId}</span>
        <span className="rounded-full border border-slate-600 px-2 py-1">Engine · {report.versions.engine}</span>
        <span className="rounded-full border border-slate-600 px-2 py-1">Contract · {report.versions.contract}</span>
      </div>
      <p className="mt-3 text-sm text-slate-300">{report.decision.clinical_summary}</p>
    </section>
  );
}
