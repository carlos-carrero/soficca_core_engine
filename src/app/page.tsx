'use client';

import { useMemo, useState } from 'react';

import { CaseIntakePanel } from '@/components/cardio/case-intake-panel';
import { CaseSummary } from '@/components/cardio/case-summary';
import { DecisionCard } from '@/components/cardio/decision-card';
import { CardioHeader } from '@/components/cardio/header';
import { NextStepsCard } from '@/components/cardio/next-steps-card';
import { SafetyCard } from '@/components/cardio/safety-card';
import { TraceCard } from '@/components/cardio/trace-card';
import { cardioScenarios } from '@/lib/cardio-mocks';
import type { CardioScenarioId } from '@/lib/cardio-types';

export default function HomePage() {
  const [scenarioId, setScenarioId] = useState<CardioScenarioId>('ROUTINE_REVIEW');

  const scenario = useMemo(
    () => cardioScenarios.find((item) => item.id === scenarioId) ?? cardioScenarios[0],
    [scenarioId],
  );

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1500px] flex-col gap-5 px-4 py-6 md:px-6 lg:px-8">
      <CardioHeader />

      <div className="grid gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
        <CaseIntakePanel scenarios={cardioScenarios} selectedId={scenario.id} onChangeScenario={setScenarioId} />

        <section className="space-y-5">
          <DecisionCard report={scenario.report} />
          <CaseSummary report={scenario.report} scenarioId={scenario.id} />
          <SafetyCard report={scenario.report} />
          <NextStepsCard report={scenario.report} />
          <TraceCard report={scenario.report} />
        </section>
      </div>
    </main>
  );
}
