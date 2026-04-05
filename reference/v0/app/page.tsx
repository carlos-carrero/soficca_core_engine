"use client"

import { useState, useCallback } from "react"
import { Header } from "@/components/soficca/header"
import { CaseInput } from "@/components/soficca/case-input"
import { EngineResults } from "@/components/soficca/engine-results"
import { DEMO_SCENARIOS, getScenarioById } from "@/lib/demo-scenarios"
import type { DemoScenario, EngineResult } from "@/lib/soficca-types"

export default function SoficcaDemo() {
  // Default to Emergency scenario as specified
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario>(
    DEMO_SCENARIOS.find((s) => s.id === "emergency") || DEMO_SCENARIOS[0]
  )
  const [result, setResult] = useState<EngineResult | null>(
    selectedScenario.result
  )
  const [isLoading, setIsLoading] = useState(false)

  const handleScenarioChange = useCallback((scenario: DemoScenario) => {
    setSelectedScenario(scenario)
    // Don't automatically run - let user click the button
    setResult(null)
  }, [])

  const handleRunEvaluation = useCallback(async () => {
    setIsLoading(true)
    // Simulate engine evaluation delay
    await new Promise((resolve) => setTimeout(resolve, 800))
    setResult({
      ...selectedScenario.result,
      technicalTrace: {
        ...selectedScenario.result.technicalTrace,
        timestamp: new Date().toISOString(),
        rawPayload: selectedScenario.input,
      },
    })
    setIsLoading(false)
  }, [selectedScenario])

  const handleReset = useCallback(() => {
    const defaultScenario =
      DEMO_SCENARIOS.find((s) => s.id === "emergency") || DEMO_SCENARIOS[0]
    setSelectedScenario(defaultScenario)
    setResult(defaultScenario.result)
  }, [])

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header />

      <main className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col lg:flex-row">
        {/* Left Column: Case Input - Secondary */}
        <div className="w-full border-b border-border lg:w-[380px] lg:border-b-0 lg:border-r">
          <CaseInput
            selectedScenario={selectedScenario}
            onScenarioChange={handleScenarioChange}
            onRunEvaluation={handleRunEvaluation}
            onReset={handleReset}
            isLoading={isLoading}
          />
        </div>

        {/* Right Column: Engine Results */}
        <div className="flex-1">
          <EngineResults result={result} isLoading={isLoading} />
        </div>
      </main>
    </div>
  )
}
