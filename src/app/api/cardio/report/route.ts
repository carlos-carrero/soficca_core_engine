import { NextResponse } from 'next/server';

import { getFallbackReport } from '@/lib/cardio-mocks';
import type { CardioPayload, CardioScenarioId } from '@/lib/cardio-types';

type RouteRequestBody = {
  payload?: CardioPayload;
  scenarioId?: CardioScenarioId;
};

const BACKEND_URL = 'http://127.0.0.1:8000/v1/cardio/report';

function extractPayload(body: unknown): { payload: CardioPayload | null; scenarioId?: CardioScenarioId } {
  if (!body || typeof body !== 'object') {
    return { payload: null };
  }

  const typed = body as RouteRequestBody;
  if (!typed.payload || typeof typed.payload !== 'object') {
    return { payload: null, scenarioId: typed.scenarioId };
  }

  return { payload: typed.payload, scenarioId: typed.scenarioId };
}

export async function POST(req: Request) {
  let parsed: { payload: CardioPayload | null; scenarioId?: CardioScenarioId } = { payload: null };

  try {
    const body = await req.json();
    parsed = extractPayload(body);

    if (!parsed.payload) {
      return NextResponse.json(getFallbackReport(parsed.scenarioId), { status: 200 });
    }

    const upstream = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.payload),
      cache: 'no-store',
    });

    if (!upstream.ok) {
      return NextResponse.json(getFallbackReport(parsed.scenarioId), { status: 200 });
    }

    const backendJson = await upstream.json();
    return NextResponse.json(backendJson, { status: 200 });
  } catch {
    return NextResponse.json(getFallbackReport(parsed.scenarioId), { status: 200 });
  }
}
