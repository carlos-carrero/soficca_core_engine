import type { CardioScenario, CardioScenarioId } from '@/lib/cardio-types';

type CaseIntakePanelProps = {
  scenarios: CardioScenario[];
  selectedId: CardioScenarioId;
  onChangeScenario: (id: CardioScenarioId) => void;
};

export function CaseIntakePanel({ scenarios, selectedId, onChangeScenario }: CaseIntakePanelProps) {
  return (
    <section className="rounded-2xl border border-slate-700/60 bg-panelSoft/80 p-5 shadow-panel">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-100">Case Intake (Editable Demo Surface)</h2>
        <p className="text-xs text-slate-400">Secondary panel for scenario simulation only.</p>
      </div>

      <label className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-400">Scenario</label>
      <select
        value={selectedId}
        onChange={(e) => onChangeScenario(e.target.value as CardioScenarioId)}
        className="mb-5 w-full rounded-lg border border-slate-600 bg-slate-950/80 px-3 py-2 text-sm text-slate-100 outline-none ring-accent focus:ring"
      >
        {scenarios.map((scenario) => (
          <option key={scenario.id} value={scenario.id}>
            {scenario.label}
          </option>
        ))}
      </select>

      <div className="grid gap-3">
        <label className="text-xs text-slate-400">
          Presenting Complaint
          <input className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm" value="Chest pain" readOnly />
        </label>
        <label className="text-xs text-slate-400">
          Structured Intake Notes
          <textarea
            className="mt-1 h-24 w-full resize-none rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm"
            value="Structured data only. No conversational or chatbot flow."
            readOnly
          />
        </label>
      </div>
    </section>
  );
}
