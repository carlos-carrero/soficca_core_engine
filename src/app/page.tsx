'use client';

import { useMemo, useState } from 'react';

import { CaseInput } from '@/components/soficca/case-input';
import { EngineResults } from '@/components/soficca/engine-results';
import { Header } from '@/components/soficca/header';
import { getDefaultScenario, mapReportToEngineViewModel } from '@/lib/cardio-ui-adapter';
import { cardioScenarios, getScenarioById } from '@/lib/cardio-mocks';
import type { CardioPayload, CardioScenarioId } from '@/lib/cardio-types';

function formatPayload(payload: CardioPayload): string {
  return JSON.stringify(payload, null, 2);
}

export default function HomePage() {
  const defaultScenario = useMemo(() => getDefaultScenario(cardioScenarios), []);
  const [scenarioId, setScenarioId] = useState<CardioScenarioId>(defaultScenario.id);
  const [payloadJson, setPayloadJson] = useState<string>(formatPayload(defaultScenario.request));
  const [isRunning, setIsRunning] = useState(false);
  const [statusMessage, setStatusMessage] = useState(
    'Ready in backend bridge mode. Select a scenario to preload payload, then run evaluation.'
  );
  const [lastEvaluated, setLastEvaluated] = useState<ReturnType<typeof mapReportToEngineViewModel> | null>(null);

  const scenario = useMemo(() => getScenarioById(scenarioId), [scenarioId]);

  function onChangeScenario(id: CardioScenarioId) {
    const nextScenario = getScenarioById(id);
    setScenarioId(id);
    setPayloadJson(formatPayload(nextScenario.request));
    setStatusMessage(`Loaded ${nextScenario.label}. Click Run Evaluation to execute against /api/cardio/report.`);
  }

  function onReset() {
    const nextScenario = getDefaultScenario(cardioScenarios);
    setScenarioId(nextScenario.id);
    setPayloadJson(formatPayload(nextScenario.request));
    setStatusMessage('Reset complete. Payload preloaded; click Run Evaluation to refresh right-side results.');
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
    const startedAt = Date.now();
    setStatusMessage('Submitting payload to /api/cardio/report ...');

    try {
      const response = await fetch('/api/cardio/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload: parsedPayload, scenarioId: scenario.id }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const nextReport = await response.json();
      const endedAt = Date.now();
      setLastEvaluated(
        mapReportToEngineViewModel(nextReport, parsedPayload, new Date(endedAt).toISOString(), endedAt - startedAt)
      );
      setStatusMessage('Evaluation complete. Right-side panel now reflects the latest evaluated report.');
    } catch (error) {
      setStatusMessage(`Evaluation failed. Preserving last evaluated report. ${(error as Error).message}`);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header />

      <main className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col lg:flex-row">
        <div className="w-full border-b border-border lg:w-[380px] lg:border-b-0 lg:border-r">
          <CaseInput
            scenarios={cardioScenarios}
            selectedScenarioId={scenarioId}
            payloadJson={payloadJson}
            statusMessage={statusMessage}
            onScenarioChange={onChangeScenario}
            onPayloadChange={setPayloadJson}
            onRunEvaluation={onRunEvaluation}
            onReset={onReset}
            isLoading={isRunning}
          />
        </div>

        <div className="flex-1">
          <EngineResults result={lastEvaluated} isLoading={isRunning} />
        </div>
      </main>
    </div>
  );
}
