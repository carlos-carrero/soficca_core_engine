import { NextResponse } from 'next/server';

import type { CardioPayload } from '@/lib/cardio-types';

type RouteRequestBody = {
  payload?: CardioPayload;
};

const BACKEND_URL = 'https://soficca-core-engine.onrender.com/v1/cardio/report';

function extractPayload(body: unknown): { payload: CardioPayload | null } {
  if (!body || typeof body !== 'object') {
    return { payload: null };
  }

  const typed = body as RouteRequestBody;
  if (!typed.payload || typeof typed.payload !== 'object') {
    return { payload: null };
  }

  return { payload: typed.payload };
}

export async function POST(req: Request) {
  let parsed: { payload: CardioPayload | null } = { payload: null };

  try {
    const body = await req.json();
    parsed = extractPayload(body);

    if (!parsed.payload) {
      return NextResponse.json({ error: 'Invalid request body: expected { payload }' }, { status: 400 });
    }

    const upstream = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.payload),
      cache: 'no-store',
    });

    if (!upstream.ok) {
      const contentType = upstream.headers.get('content-type') ?? 'application/json';
      const raw = await upstream.text();
      return new Response(raw, {
        status: upstream.status,
        headers: { 'content-type': contentType },
      });
    }

    const backendJson = await upstream.json();
    return NextResponse.json(backendJson, { status: 200 });
  } catch {
    return NextResponse.json({ error: 'Backend engine unreachable' }, { status: 502 });
  }
}
