import type { CardioScenario, CardioScenarioId } from '@/lib/cardio-types';

type CaseIntakePanelProps = {
  scenarios: CardioScenario[];
  selectedId: CardioScenarioId;
  payloadJson: string;
  statusMessage: string;
  isRunning: boolean;
  onChangeScenario: (id: CardioScenarioId) => void;
  onPayloadChange: (payloadJson: string) => void;
  onRunEvaluation: () => void;
};

export function CaseIntakePanel({
  scenarios,
  selectedId,
  payloadJson,
  statusMessage,
  isRunning,
  onChangeScenario,
  onPayloadChange,
  onRunEvaluation,
}: CaseIntakePanelProps) {
  return (
    <section className="rounded-2xl border border-slate-700/60 bg-panelSoft/80 p-5 shadow-panel">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-100">Case Intake (Editable Demo Surface)</h2>
        <p className="text-xs text-slate-400">Structured payload in, deterministic report out.</p>
      </div>

      <label className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-400">Scenario</label>
      <select
        value={selectedId}
        onChange={(e) => onChangeScenario(e.target.value as CardioScenarioId)}
        className="mb-4 w-full rounded-lg border border-slate-600 bg-slate-950/80 px-3 py-2 text-sm text-slate-100 outline-none ring-accent focus:ring"
      >
        {scenarios.map((scenario) => (
          <option key={scenario.id} value={scenario.id}>
            {scenario.label}
          </option>
        ))}
      </select>

      <button
        type="button"
        onClick={onRunEvaluation}
        disabled={isRunning}
        className="mb-5 w-full rounded-xl border border-cyan-300/70 bg-cyan-300 px-4 py-3 text-base font-bold tracking-wide text-slate-950 shadow-[0_0_0_1px_rgba(255,255,255,0.2),0_0_35px_rgba(34,211,238,0.35)] transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isRunning ? 'Running evaluation...' : 'Run Evaluation'}
      </button>

      <label className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-400">Cardio payload JSON</label>
      <textarea
        className="h-64 w-full resize-none rounded-lg border border-slate-700 bg-slate-950/70 p-3 font-mono text-xs text-slate-100 outline-none ring-accent focus:ring"
        value={payloadJson}
        onChange={(e) => onPayloadChange(e.target.value)}
        spellCheck={false}
      />

      <p className="mt-3 text-xs text-slate-400">{statusMessage}</p>
    </section>
  );
}
