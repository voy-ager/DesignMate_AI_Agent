// lib/api.ts
// All FastAPI calls from the frontend.
// Single source of truth for API interaction.
// REAL API SWITCH: change API_BASE to your deployed backend URL when ready.

import { AnalyzeResponse, RefineResponse, Metrics } from "./types"

export const API_BASE = "http://localhost:8000"

export async function analyzeRoom(
  file: File,
  budget: number,
  style: string
): Promise<AnalyzeResponse> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("budget", budget.toString())
  formData.append("style", style)

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || "Analysis failed")
  }

  return response.json()
}

export async function refineDesign(
  sessionId: string,
  message: string
): Promise<RefineResponse> {
  const formData = new FormData()
  formData.append("session_id", sessionId)
  formData.append("message", message)

  const response = await fetch(`${API_BASE}/refine`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || "Refinement failed")
  }

  return response.json()
}

export async function getMetrics(sessionId: string): Promise<Metrics> {
  const response = await fetch(`${API_BASE}/metrics/${sessionId}`)
  if (!response.ok) throw new Error("Failed to fetch metrics")
  const data = await response.json()
  return data.metrics
}

export function createSSEConnection(
  sessionId: string,
  onMessage: (log: unknown) => void,
  onError?: (error: Event) => void
): EventSource {
  // Pitfall 3: SSE connection with keepalive handling
  const eventSource = new EventSource(
    `${API_BASE}/stream/${sessionId}`
  )

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      // Skip keepalive pings
      if (data.event === "keepalive") return
      onMessage(data)
    } catch {
      // Skip malformed events
    }
  }

  eventSource.onerror = (error) => {
    if (onError) onError(error)
    // Auto-close on error to prevent infinite reconnect
    eventSource.close()
  }

  return eventSource
}