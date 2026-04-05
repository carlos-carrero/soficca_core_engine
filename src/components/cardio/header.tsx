export function CardioHeader() {
  return (
    <header className="rounded-2xl border border-slate-700/60 bg-panel/80 p-6 shadow-panel backdrop-blur">
      <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Soficca · Cardio Demo</p>
      <h1 className="mt-3 font-[var(--font-space-grotesk)] text-3xl font-semibold text-slate-100 md:text-4xl">
        Clinical Decision Infrastructure Console
      </h1>
      <p className="mt-3 max-w-3xl text-sm text-slate-300">
        Deterministic triage visualization in local mock mode (no backend integration in this step).
      </p>
    </header>
  );
}
