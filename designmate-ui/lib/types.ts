// lib/types.ts
// TypeScript interfaces that exactly mirror the Python AppState schema.
// Every component imports from here — never define types inline.

export interface RoomDimensions {
  width_ft: number
  length_ft: number
  area_sqft: number
  ceiling_height_ft: number
}

export interface RoomAnalysis {
  room_type: string
  dimensions: RoomDimensions
  windows: Array<{
    wall: string
    width_ft: number
    height_ft: number
    natural_light: string
  }>
  doors: Array<{ wall: string; width_ft: number }>
  lighting: { natural_direction: string; quality: string }
  floor_type: string
  wall_color: string
  existing_features: string[]
  constraints: {
    max_sofa_width_inches: number
    walkway_clearance_inches: number
  }
}

export interface ColorPalette {
  primary: string
  secondary: string
  accent: string
}

export interface RequiredItem {
  category: string
  max_width_inches: number | null
  style_query: string
}

export interface DesignConcept {
  concept_name: string
  style_tags: string[]
  color_palette: ColorPalette
  budget_total: number
  budget_allocation: {
    seating: number
    tables: number
    textiles: number
    accessories: number
  }
  required_items: RequiredItem[]
  concept_index: number
}

export interface PlannedItem {
  category: string
  max_width_inches: number | null
  style_query: string
  budget_ceiling: number
}

export interface FurniturePlanConcept {
  concept_name: string
  concept_index: number
  style_tags: string[]
  color_palette: ColorPalette
  planned_items: PlannedItem[]
  total_budget: number
}

export interface FurniturePlan {
  concepts: FurniturePlanConcept[]
}

export interface ProductDimensions {
  width: number
  depth: number
  height: number
}

export interface SourcedProduct {
  product_id: string
  category: string
  name: string
  price: number
  dimensions: ProductDimensions
  style_descriptor: string
  purchase_url: string
  in_stock: boolean
  similarity_score: number
  within_budget: boolean
  budget_ceiling: number
}

export interface SourcedConcept {
  concept_name: string
  concept_index: number
  style_tags: string[]
  color_palette: ColorPalette
  items: SourcedProduct[]
  total_cost: number
  budget_remaining: number
}

export interface RenderUrl {
  concept_name: string
  concept_index: number
  image_url: string
  prompt_used: string
  mode: string
}

export interface AgentLog {
  timestamp: string
  agent: string
  event: string
  level: "info" | "warning" | "error" | "success"
  message: string
  data: Record<string, unknown>
}

export interface StageTimings {
  vision?: number
  planning?: number
  optimization?: number
  retrieval?: number
  rendering?: number
}

export interface Metrics {
  budget_accuracy: number
  concepts_within_budget: number
  concepts_over_budget: number
  total_items_evaluated: number
  style_coherence_avg: number
  style_coherence_min: number
  style_coherence_max: number
  coherence_target_met: boolean
  constraint_satisfaction_rate: number
  stage_timings: StageTimings
  total_latency_seconds: number
  avg_concept_overlap: number
  diversity_target_met: boolean
  pairwise_overlap_scores: number[]
  mode: string
}

export interface AnalyzeResponse {
  session_id: string
  status: string
  mode: string
  room_analysis: RoomAnalysis
  design_concepts: DesignConcept[]
  furniture_plan: FurniturePlan
  sourced_products: SourcedConcept[]
  render_urls: RenderUrl[]
  agent_logs: AgentLog[]
  metrics: Metrics
  error: string | null
}

export interface RefineResponse {
  session_id: string
  status: string
  mode: string
  dialogue_history: Array<{ role: string; content: string }>
  sourced_products: SourcedConcept[]
  render_urls: RenderUrl[]
  agent_logs: AgentLog[]
  metrics: Metrics
  budget: number
  style: string
  error: string | null
}

export type StyleMood =
  | "modern"
  | "minimalist"
  | "scandinavian"
  | "industrial"
  | "contemporary"
  | "rustic"
  | "bohemian"
  | "mid-century"