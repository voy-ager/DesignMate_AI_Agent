// lib/types.ts
export interface RoomDimensions {
  width_ft: number; length_ft: number; area_sqft: number; ceiling_height_ft: number
}
export interface RoomAnalysis {
  room_type: string; dimensions: RoomDimensions
  windows: Array<{ wall: string; width_ft: number; height_ft: number; natural_light: string }>
  doors: Array<{ wall: string; width_ft: number }>
  lighting: { natural_direction: string; quality: string }
  floor_type: string; wall_color: string; existing_features: string[]
  constraints: { max_sofa_width_inches: number; walkway_clearance_inches: number }
}
export interface ColorPalette { primary: string; secondary: string; accent: string }
export interface RequiredItem { category: string; max_width_inches: number | null; style_query: string }
export interface DesignConcept {
  concept_name: string; style_tags: string[]; color_palette: ColorPalette
  budget_total: number
  budget_allocation: { seating: number; tables: number; textiles: number; accessories: number }
  required_items: RequiredItem[]; concept_index: number
}
export interface PlannedItem { category: string; max_width_inches: number | null; style_query: string; budget_ceiling: number }
export interface FurniturePlanConcept {
  concept_name: string; concept_index: number; style_tags: string[]
  color_palette: ColorPalette; planned_items: PlannedItem[]; total_budget: number
}
export interface FurniturePlan { concepts: FurniturePlanConcept[] }
export interface ProductDimensions { width: number; depth: number; height: number }
export interface SourcedProduct {
  product_id: string; category: string; name: string; price: number
  dimensions: ProductDimensions; style_descriptor: string; purchase_url: string
  in_stock: boolean; similarity_score: number; within_budget: boolean; budget_ceiling: number
}
export interface SourcedConcept {
  concept_name: string; concept_index: number; style_tags: string[]
  color_palette: ColorPalette; items: SourcedProduct[]; total_cost: number; budget_remaining: number
}
export interface RenderUrl { concept_name: string; concept_index: number; image_url: string; prompt_used: string; mode: string }
export interface AgentLog {
  timestamp: string; agent: string; event: string
  level: "info" | "warning" | "error" | "success"; message: string; data: Record<string, unknown>
}
export interface StageTimings { vision?: number; planning?: number; optimization?: number; retrieval?: number; rendering?: number }

// ── Metrics ───────────────────────────────────────────────────────────────────
export interface LatencyMetrics {
  per_agent_seconds: Record<string, number>
  speed_grades: Record<string, "fast" | "normal" | "slow">
  total_seconds: number; slowest_agent: string | null; slowest_seconds: number
  agents_completed: number; agents_total: number
}
export interface ConceptBudgetResult {
  concept_name: string; total_cost: number; budget: number
  utilization_pct: number; budget_remaining: number; within_budget: boolean
  items_within_budget: number; items_over_budget: number
}
export interface BudgetMetrics {
  accuracy: number; accuracy_pct: number; total_items_evaluated: number
  items_within_budget: number; items_over_budget: number
  avg_concept_cost: number; min_concept_cost: number; max_concept_cost: number
  budget_target: number; concepts_within_budget: number; concepts_over_budget: number
  per_concept: ConceptBudgetResult[]
}
export interface ConceptCoherenceResult {
  concept_name: string; coherence: number; coherence_pct: number; target_met: boolean; num_items: number
}
export interface StyleCoherenceMetrics {
  avg: number; avg_pct: number; min: number; max: number
  target: number; target_met: boolean; concepts_above_target: number; per_concept: ConceptCoherenceResult[]
}
export interface ConstraintMetrics {
  overall_rate: number; overall_pct: number
  spatial_pass_rate: number; spatial_pass_pct: number
  spatial_checks_passed: number; spatial_checks_failed: number; spatial_checks_total: number
  budget_ceiling_triggers: number; zero_budget_categories: number
  budget_accuracy: number; budget_accuracy_pct: number
}
export interface ConceptPlanResult {
  concept_name: string; style_tags: string[]; items_planned: number; budget_total: number
}
export interface PlanningMetrics {
  concepts_generated: number; avg_items_per_concept: number
  total_style_tags: number; unique_style_tags: string[]; unique_style_tag_count: number
  style_tag_diversity: number; style_tag_diversity_pct: number
  planning_mode: string; api_fallback_triggered: boolean
  planning_latency_seconds: number; per_concept: ConceptPlanResult[]
}
export interface TopEvent { event: string; count: number }
export interface ToolMetric { calls: number; failures: number; success_rate: number; top_events: TopEvent[]; latency_seconds: number }
export interface PineconeMetric { searches: number; hits: number; misses: number; hit_rate: number; hit_rate_pct: number; top_events: TopEvent[]; latency_seconds: number }
export interface FluxMetric { calls: number; real_renders: number; mock_renders: number; fallbacks: number; success_rate: number; success_pct: number; top_events: TopEvent[]; latency_seconds: number }
export interface ToolCallMetrics {
  total_calls: number; total_failures: number; overall_success_rate: number; overall_success_pct: number
  groq_vision: ToolMetric; groq_planning: ToolMetric; pinecone: PineconeMetric; huggingface_flux: FluxMetric
}
export interface MemoryMetrics {
  session_state_completeness: number; session_state_completeness_pct: number
  populated_state_fields: string[]; total_state_fields: number
  dialogue_turns: number; refinement_cycles: number
  has_active_session: boolean; state_size_kb: number
  total_log_events_stored: number; retry_count: number; mode: string
}
export interface ActionMetrics {
  stages_started: number; stages_completed: number; stage_completion_rate: number
  total_decisions: number; correct_decisions: number; decision_accuracy: number; decision_accuracy_pct: number
  products_selected: number; products_rejected: number; api_calls_total: number
  spatial_checks_passed: number; spatial_checks_failed: number
  budget_ceiling_triggers: number; pipeline_retries: number; fallback_triggered: boolean
}
export interface PairwiseOverlap { pair: string; overlap: number; overlap_pct: number; diverse: boolean }
export interface ConceptDiversityMetrics {
  diversity_score: number; diversity_score_pct: number
  avg_product_overlap: number; avg_tag_overlap: number
  diversity_target_met: boolean; pairwise_overlaps: PairwiseOverlap[]
}
export interface RetrievalPrecisionMetrics {
  fill_rate: number; fill_rate_pct: number
  total_searches: number; products_selected: number; products_rejected: number
  over_budget_picks: number; no_match_count: number
  category_precision: Record<string, number>; retrieval_latency_seconds: number
}
export interface AgentErrorInfo { errors: number; warnings: number; messages: string[] }
export interface PipelineHealthMetrics {
  completed: boolean; status: string; error: string | null
  handoff_success_rate: number; handoff_success_pct: number; handoffs: Record<string, boolean>
  error_count: number; warning_count: number; error_rate: number; error_rate_pct: number
  errors_by_agent: Record<string, AgentErrorInfo>
  agents_succeeded: number; agents_failed: number; total_log_events: number
}
export interface MetricsSummary {
  overall_score: number; overall_score_pct: number
  autonomy_score: number; autonomy_score_pct: number
  budget_accuracy_pct: number; style_coherence_pct: number
  constraint_satisfaction_pct: number; planning_diversity_pct: number
  retrieval_fill_rate_pct: number; concept_diversity_pct: number
  handoff_success_pct: number; tool_success_pct: number; action_accuracy_pct: number
  total_latency_seconds: number; pipeline_status: string; mode: string
}
export interface Metrics {
  latency:               LatencyMetrics
  budget:                BudgetMetrics
  style_coherence:       StyleCoherenceMetrics
  constraint_satisfaction: ConstraintMetrics
  planning:              PlanningMetrics
  tool_calls:            ToolCallMetrics
  memory:                MemoryMetrics
  actions:               ActionMetrics
  concept_diversity:     ConceptDiversityMetrics
  retrieval_precision:   RetrievalPrecisionMetrics
  pipeline_health:       PipelineHealthMetrics
  summary:               MetricsSummary
}

// ── API responses ─────────────────────────────────────────────────────────────
export interface AnalyzeResponse {
  session_id: string; status: string; mode: string
  room_analysis: RoomAnalysis; design_concepts: DesignConcept[]
  furniture_plan: FurniturePlan; sourced_products: SourcedConcept[]
  render_urls: RenderUrl[]; agent_logs: AgentLog[]; metrics: Metrics; error: string | null
}
export interface RefineResponse {
  session_id: string; status: string; mode: string
  dialogue_history: Array<{ role: string; content: string }>
  sourced_products: SourcedConcept[]; render_urls: RenderUrl[]
  agent_logs: AgentLog[]; metrics: Metrics; budget: number; style: string; error: string | null
}
export type StyleMood = "modern" | "minimalist" | "scandinavian" | "industrial" | "contemporary" | "rustic" | "bohemian" | "mid-century"