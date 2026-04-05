'use client';

import { useMemo, useState } from 'react';

import { CaseIntakePanel } from '@/components/cardio/case-intake-panel';
import { CaseSummary } from '@/components/cardio/case-summary';
import { DecisionCard } from '@/components/cardio/decision-card';
import { CardioHeader } from '@/components/cardio/header';
import { NextStepsCard } from '@/components/cardio/next-steps-card';
import { SafetyCard } from '@/components/cardio/safety-card';
import { TraceCard } from '@/components/cardio/trace-card';
import { cardioScenarios, getScenarioById } from '@/lib/cardio-mocks';
import type { CardioPayload, CardioReport, CardioScenarioId } from '@/lib/cardio-types';

function formatPayload(payload: CardioPayload): string {
  return JSON.stringify(payload, null, 2);
}

export default function HomePage() {
  const [scenarioId, setScenarioId] = useState<CardioScenarioId>('ROUTINE_REVIEW');
  const [isRunning, setIsRunning] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Ready in local+backend bridge mode.');

  const scenario = useMemo(() => getScenarioById(scenarioId), [scenarioId]);

  const [payloadJson, setPayloadJson] = useState<string>(formatPayload(scenario.request));
  const [report, setReport] = useState<CardioReport>(scenario.report);

  function onChangeScenario(id: CardioScenarioId) {
    const nextScenario = getScenarioById(id);
    setScenarioId(id);
    setPayloadJson(formatPayload(nextScenario.request));
    setReport(nextScenario.report);
    setStatusMessage(`Loaded ${id}. Click Run Evaluation to execute against backend via /api/cardio/report.`);
  }

  async function onRunEvaluation() {
    let parsedPayload: CardioPayload;
    try {
      parsedPayload = JSON.parse(payloadJson) as CardioPayload;
      if (!parsedPayload || typeof parsedPayload !== 'object' || typeof parsedPayload.state !== 'object') {
        throw new Error('payload must include an object state');
      }
    } catch (error) {
      setStatusMessage(`Invalid JSON payload: ${(error as Error).message}`);
      return;
    }

    setIsRunning(true);
    setStatusMessage('Submitting payload to /api/cardio/report ...');

    try {
      const response = await fetch('/api/cardio/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload: parsedPayload, scenarioId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const nextReport = (await response.json()) as CardioReport;
      setReport(nextReport);
      setStatusMessage(`Evaluation complete. ok=${String(nextReport.ok)}.`);
    } catch (error) {
      setStatusMessage(`Evaluation failed: ${(error as Error).message}`);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1500px] flex-col gap-5 px-4 py-6 md:px-6 lg:px-8">
      <CardioHeader />

      <div className="grid gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
        <CaseIntakePanel
          scenarios={cardioScenarios}
          selectedId={scenarioId}
          payloadJson={payloadJson}
          statusMessage={statusMessage}
          isRunning={isRunning}
          onChangeScenario={onChangeScenario}
          onPayloadChange={setPayloadJson}
          onRunEvaluation={onRunEvaluation}
        />

        <section className="space-y-5">
          <DecisionCard report={report} />
          <CaseSummary report={report} scenarioId={scenarioId} />
          <SafetyCard report={report} />
          <NextStepsCard report={report} />
          <TraceCard report={report} />
        </section>
      </div>
    </main>
  );
}
