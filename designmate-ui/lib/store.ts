// lib/store.ts
import { create } from "zustand"
import {
  AnalyzeResponse,
  SourcedConcept,
  RenderUrl,
  AgentLog,
  Metrics,
  StyleMood,
  RefineResponse,
} from "./types"

interface DesignMateStore {
  sessionId: string | null
  isLoading: boolean
  error: string | null
  budget: number
  style: StyleMood
  imageFile: File | null
  imagePreview: string | null
  analyzeResponse: AnalyzeResponse | null
  sourcedProducts: SourcedConcept[]
  renderUrls: RenderUrl[]
  agentLogs: AgentLog[]
  metrics: Metrics | null
  selectedConceptIndex: number
  viewMode: "render" | "blueprint"
  selectedProductId: string | null
  isRefining: boolean
  refineMessage: string

  setBudget: (budget: number) => void
  setStyle: (style: StyleMood) => void
  setImageFile: (file: File, preview: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setAnalyzeResponse: (response: AnalyzeResponse) => void
  setSelectedConcept: (index: number) => void
  setViewMode: (mode: "render" | "blueprint") => void
  setSelectedProduct: (productId: string | null) => void
  appendLog: (log: AgentLog) => void
  setRefineMessage: (message: string) => void
  setRefining: (refining: boolean) => void
  applyRefineResponse: (response: RefineResponse) => void
  applyPartialUpdate: (data: Partial<AnalyzeResponse>) => void
  reset: () => void
}

const initialState = {
  sessionId: null,
  isLoading: false,
  error: null,
  budget: 2000,
  style: "modern" as StyleMood,
  imageFile: null,
  imagePreview: null,
  analyzeResponse: null,
  sourcedProducts: [],
  renderUrls: [],
  agentLogs: [],
  metrics: null,
  selectedConceptIndex: 0,
  viewMode: "render" as const,
  selectedProductId: null,
  isRefining: false,
  refineMessage: "",
}

export const useStore = create<DesignMateStore>((set) => ({
  ...initialState,

  setBudget: (budget) => set({ budget }),
  setStyle: (style) => set({ style }),
  setImageFile: (file, preview) =>
    set({ imageFile: file, imagePreview: preview }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  setAnalyzeResponse: (response) =>
    set({
      analyzeResponse: response,
      sessionId: response.session_id,
      sourcedProducts: response.sourced_products,
      renderUrls: response.render_urls,
      agentLogs: response.agent_logs,
      metrics: response.metrics,
      selectedConceptIndex: 0,
      error: null,
    }),

  setSelectedConcept: (index) => set({ selectedConceptIndex: index }),
  setViewMode: (viewMode) => set({ viewMode }),
  setSelectedProduct: (selectedProductId) => set({ selectedProductId }),

  appendLog: (log) =>
    set((state) => ({
      agentLogs: [...state.agentLogs, log].slice(-100),
    })),

  setRefineMessage: (refineMessage) => set({ refineMessage }),
  setRefining: (isRefining) => set({ isRefining }),

  applyRefineResponse: (response) =>
    set({
      sourcedProducts: response.sourced_products,
      renderUrls: response.render_urls,
      agentLogs: response.agent_logs,
      metrics: response.metrics,
      isRefining: false,
      refineMessage: "",
      error: null,
    }),

  applyPartialUpdate: (data) =>
    set((state) => ({
      sourcedProducts: data.sourced_products ?? state.sourcedProducts,
      renderUrls:      data.render_urls      ?? state.renderUrls,
      agentLogs:       data.agent_logs       ?? state.agentLogs,
      metrics:         data.metrics          ?? state.metrics,
    })),

  reset: () => set(initialState),
}))