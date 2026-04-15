// components/MetricsDashboard.tsx
"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, ChevronRight } from "lucide-react"
import { Metrics } from "@/lib/types"

const SPEED_COLORS: Record<string, string> = {
  fast:   "text-emerald-400",
  normal: "text-amber-400",
  slow:   "text-red-400",
}

const SPEED_BG: Record<string, string> = {
  fast:   "bg-emerald-400/20 border-emerald-400/40",
  normal: "bg-amber-400/20 border-amber-400/40",
  slow:   "bg-red-400/20 border-red-400/40",
}

function Bar({ value, max = 100, color = "bg-emerald-400" }: { value: number; max?: number; color?: string }) {
  const pct = Math.min((value / max) * 100, 100)
  return (
    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${color}`}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </div>
  )
}

function Gauge({ label, pct, color = "text-emerald-400" }: { label: string; pct: number; color?: string }) {
  const barColor = pct >= 75 ? "bg-emerald-400" : pct >= 50 ? "bg-amber-400" : "bg-red-400"
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className={color}>{pct}%</span>
      </div>
      <Bar value={pct} color={barColor} />
    </div>
  )
}

function Row({ label, value, mono = true }: { label: string; value: string | number; mono?: boolean }) {
  return (
    <div className="flex justify-between text-xs py-0.5">
      <span className="text-slate-500">{label}</span>
      <span className={`text-slate-300 ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  )
}

function Badge({ text, variant }: { text: string; variant: "success" | "warn" | "error" | "info" }) {
  const styles = {
    success: "bg-emerald-400/20 text-emerald-400 border-emerald-400/40",
    warn:    "bg-amber-400/20 text-amber-400 border-amber-400/40",
    error:   "bg-red-400/20 text-red-400 border-red-400/40",
    info:    "bg-blue-400/20 text-blue-400 border-blue-400/40",
  }
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded border ${styles[variant]}`}>{text}</span>
  )
}

function Section({ title, children, defaultOpen = false }: {
  title: string; children: React.ReactNode; defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border-t border-slate-700/50">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5
                   text-xs font-semibold text-slate-400 uppercase tracking-wider
                   hover:text-slate-200 transition-colors"
      >
        {title}
        {open
          ? <ChevronDown size={12} className="text-slate-500" />
          : <ChevronRight size={12} className="text-slate-500" />
        }
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 space-y-2">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function MetricsDashboard({ metrics }: { metrics: Metrics }) {
  const s   = metrics.summary
  const lat = metrics.latency
  const bud = metrics.budget
  const coh = metrics.style_coherence
  const con = metrics.constraint_satisfaction
  const pln = metrics.planning
  const tc  = metrics.tool_calls
  const mem = metrics.memory
  const act = metrics.actions
  const ret = metrics.retrieval_precision
  const div = metrics.concept_diversity
  const ph  = metrics.pipeline_health

  return (
    <div className="text-xs">

      {/* ── Overview cards ── */}
      <div className="px-4 py-3 grid grid-cols-2 gap-2">
        {[
          { label: "Overall",    value: s?.overall_score_pct    ?? 0 },
          { label: "Autonomy",   value: s?.autonomy_score_pct   ?? 0 },
          { label: "Budget",     value: s?.budget_accuracy_pct  ?? 0 },
          { label: "Coherence",  value: s?.style_coherence_pct  ?? 0 },
          { label: "Retrieval",  value: s?.retrieval_fill_rate_pct ?? 0 },
          { label: "Diversity",  value: s?.concept_diversity_pct ?? 0 },
        ].map(({ label, value }) => {
          const color = value >= 75 ? "text-emerald-400" : value >= 50 ? "text-amber-400" : "text-red-400"
          return (
            <div key={label} className="bg-slate-800/60 rounded-lg p-2 space-y-1">
              <div className="text-slate-500">{label}</div>
              <div className={`text-lg font-bold font-mono ${color}`}>{value}%</div>
              <Bar value={value} color={value >= 75 ? "bg-emerald-400" : value >= 50 ? "bg-amber-400" : "bg-red-400"} />
            </div>
          )
        })}
      </div>

      {/* ── 1. Budget ── */}
      <Section title="Budget + Spend" defaultOpen>
        <Gauge label="Budget accuracy" pct={bud?.accuracy_pct ?? 0} />
        <Row label="Items within budget" value={`${bud?.items_within_budget ?? 0} / ${bud?.total_items_evaluated ?? 0}`} />
        <Row label="Concepts in budget"  value={`${bud?.concepts_within_budget ?? 0} / 3`} />
        <Row label="Avg spend"           value={`$${bud?.avg_concept_cost ?? 0}`} />
        <Row label="Min spend"           value={`$${bud?.min_concept_cost ?? 0}`} />
        <Row label="Max spend"           value={`$${bud?.max_concept_cost ?? 0}`} />
        <Row label="Budget target"       value={`$${bud?.budget_target ?? 0}`} />
        {bud?.per_concept?.map(c => (
          <div key={c.concept_name} className="pl-2 border-l border-slate-700 mt-1 space-y-0.5">
            <div className="text-slate-400 truncate">{c.concept_name}</div>
            <div className="flex justify-between">
              <span className="text-slate-500">Cost</span>
              <span className="font-mono text-slate-300">${c.total_cost} ({c.utilization_pct}%)</span>
            </div>
            <Bar value={c.utilization_pct} color={c.within_budget ? "bg-emerald-400" : "bg-red-400"} />
          </div>
        ))}
      </Section>

      {/* ── 2. Style coherence ── */}
      <Section title="Style Coherence">
        <Gauge label="Avg coherence" pct={coh?.avg_pct ?? 0} color="text-purple-400" />
        <Row label="Min / Max" value={`${coh?.min ?? 0} / ${coh?.max ?? 0}`} />
        <Row label="Target 0.75" value="" />
        <div className="flex justify-end">
          <Badge text={coh?.target_met ? "✓ Met" : "✗ Not met"} variant={coh?.target_met ? "success" : "warn"} />
        </div>
        {coh?.per_concept?.map(c => (
          <div key={c.concept_name} className="pl-2 border-l border-slate-700 space-y-0.5">
            <div className="text-slate-400 truncate">{c.concept_name}</div>
            <Bar value={c.coherence_pct} color={c.target_met ? "bg-emerald-400" : "bg-amber-400"} />
            <div className="text-right text-slate-500">{c.coherence_pct}%</div>
          </div>
        ))}
      </Section>

      {/* ── 3. Constraint satisfaction ── */}
      <Section title="Constraint Satisfaction">
        <Gauge label="Overall satisfaction" pct={con?.overall_pct ?? 0} color="text-teal-400" />
        <Gauge label="Spatial pass rate"    pct={con?.spatial_pass_pct ?? 0} color="text-blue-400" />
        <Row label="Spatial checks"         value={`${con?.spatial_checks_passed ?? 0} pass / ${con?.spatial_checks_failed ?? 0} fail`} />
        <Row label="Budget ceilings set"    value={String(con?.budget_ceiling_triggers ?? 0)} />
        <Row label="Zero-budget categories" value={String(con?.zero_budget_categories ?? 0)} />
      </Section>

      {/* ── 4. Stage latency ── */}
      <Section title="Stage Latency">
        <Row label="Total" value={`${lat?.total_seconds ?? 0}s`} />
        <Row label="Slowest agent" value={lat?.slowest_agent ?? "—"} />
        {lat?.per_agent_seconds && Object.entries(lat.per_agent_seconds).map(([agent, t]) => {
          const grade = lat.speed_grades?.[agent] ?? "normal"
          return (
            <div key={agent} className="space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 capitalize">{agent}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-1 py-0.5 rounded border ${SPEED_BG[grade]}`}>
                    <span className={SPEED_COLORS[grade]}>{grade}</span>
                  </span>
                  <span className="font-mono text-slate-300">{t}s</span>
                </div>
              </div>
              <Bar
                value={t}
                max={lat.total_seconds}
                color={grade === "fast" ? "bg-emerald-400" : grade === "normal" ? "bg-amber-400" : "bg-red-400"}
              />
            </div>
          )
        })}
      </Section>

      {/* ── 5. Planning quality ── */}
      <Section title="Planning Quality">
        <Gauge label="Style tag diversity" pct={pln?.style_tag_diversity_pct ?? 0} color="text-purple-400" />
        <Row label="Concepts generated"    value={String(pln?.concepts_generated ?? 0)} />
        <Row label="Avg items / concept"   value={String(pln?.avg_items_per_concept ?? 0)} />
        <Row label="Unique style tags"     value={String(pln?.unique_style_tag_count ?? 0)} />
        <Row label="Planning mode"         value={pln?.planning_mode ?? "—"} />
        <Row label="Latency"               value={`${pln?.planning_latency_seconds ?? 0}s`} />
        {pln?.unique_style_tags && pln.unique_style_tags.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {pln.unique_style_tags.map(tag => (
              <span key={tag} className="text-xs px-1.5 py-0.5 bg-purple-400/20 text-purple-300 rounded border border-purple-400/30">
                {tag}
              </span>
            ))}
          </div>
        )}
      </Section>

      {/* ── 6. Tool usage ── */}
      <Section title="Tool Usage per Agent">
        <Row label="Total calls"    value={String(tc?.total_calls ?? 0)} />
        <Row label="Total failures" value={String(tc?.total_failures ?? 0)} />
        <Gauge label="Overall success" pct={Math.round((tc?.overall_success_rate ?? 0) * 100)} color="text-amber-400" />
        {[
          { key: "groq_vision",    label: "Groq Vision",     data: tc?.groq_vision },
          { key: "groq_planning",  label: "Groq Planning",   data: tc?.groq_planning },
        ].map(({ key, label, data }) => data && (
          <div key={key} className="pl-2 border-l border-slate-700 space-y-0.5">
            <div className="text-slate-400">{label}</div>
            <Row label="Calls"    value={String(data.calls)} />
            <Row label="Success"  value={`${Math.round(data.success_rate * 100)}%`} />
            <Row label="Latency"  value={`${data.latency_seconds}s`} />
            {data.top_events?.map(e => (
              <div key={e.event} className="flex justify-between text-slate-500">
                <span>{e.event}</span><span className="font-mono">{e.count}x</span>
              </div>
            ))}
          </div>
        ))}
        {tc?.pinecone && (
          <div className="pl-2 border-l border-slate-700 space-y-0.5">
            <div className="text-slate-400">Pinecone</div>
            <Row label="Searches"  value={String(tc.pinecone.searches)} />
            <Row label="Hit rate"  value={`${tc.pinecone.hit_rate_pct}%`} />
            <Row label="Latency"   value={`${tc.pinecone.latency_seconds}s`} />
          </div>
        )}
        {tc?.huggingface_flux && (
          <div className="pl-2 border-l border-slate-700 space-y-0.5">
            <div className="text-slate-400">HuggingFace FLUX</div>
            <Row label="Real renders"  value={String(tc.huggingface_flux.real_renders)} />
            <Row label="Fallbacks"     value={String(tc.huggingface_flux.fallbacks)} />
            <Row label="Success"       value={`${tc.huggingface_flux.success_pct}%`} />
            <Row label="Latency"       value={`${tc.huggingface_flux.latency_seconds}s`} />
          </div>
        )}
      </Section>

      {/* ── 7. Memory / session ── */}
      <Section title="Memory / Session">
        <Gauge label="State completeness" pct={mem?.session_state_completeness_pct ?? 0} color="text-teal-400" />
        <Row label="Dialogue turns"      value={String(mem?.dialogue_turns ?? 0)} />
        <Row label="Refinement cycles"   value={String(mem?.refinement_cycles ?? 0)} />
        <Row label="State size"          value={`${mem?.state_size_kb ?? 0} KB`} />
        <Row label="Log events stored"   value={String(mem?.total_log_events_stored ?? 0)} />
        <Row label="Retry count"         value={String(mem?.retry_count ?? 0)} />
        <Row label="Mode"                value={mem?.mode ?? "—"} />
      </Section>

      {/* ── 8. Actions ── */}
      <Section title="Actions">
        <Gauge label="Decision accuracy"  pct={act?.decision_accuracy_pct ?? 0} color="text-pink-400" />
        <Row label="Stages started"       value={String(act?.stages_started ?? 0)} />
        <Row label="Stages completed"     value={String(act?.stages_completed ?? 0)} />
        <Row label="Products selected"    value={String(act?.products_selected ?? 0)} />
        <Row label="Products rejected"    value={String(act?.products_rejected ?? 0)} />
        <Row label="API calls total"      value={String(act?.api_calls_total ?? 0)} />
        <Row label="Spatial checks"       value={`${act?.spatial_checks_passed ?? 0} pass / ${act?.spatial_checks_failed ?? 0} fail`} />
        <Row label="Budget ceilings"      value={String(act?.budget_ceiling_triggers ?? 0)} />
        <Row label="Pipeline retries"     value={String(act?.pipeline_retries ?? 0)} />
      </Section>

      {/* ── 9. Retrieval precision ── */}
      <Section title="Retrieval Precision">
        <Gauge label="Fill rate" pct={ret?.fill_rate_pct ?? 0} color="text-amber-400" />
        <Row label="Total searches"    value={String(ret?.total_searches ?? 0)} />
        <Row label="Products found"    value={String(ret?.products_selected ?? 0)} />
        <Row label="No-match count"    value={String(ret?.no_match_count ?? 0)} />
        <Row label="Over-budget picks" value={String(ret?.over_budget_picks ?? 0)} />
        <Row label="Latency"           value={`${ret?.retrieval_latency_seconds ?? 0}s`} />
        {ret?.category_precision && Object.keys(ret.category_precision).length > 0 && (
          <div className="space-y-1 pt-1">
            <div className="text-slate-500">Category precision</div>
            {Object.entries(ret.category_precision).map(([cat, prec]) => (
              <div key={cat} className="space-y-0.5">
                <div className="flex justify-between text-slate-400">
                  <span>{cat}</span>
                  <span className="font-mono">{Math.round(prec * 100)}%</span>
                </div>
                <Bar value={prec * 100} color={prec >= 0.75 ? "bg-emerald-400" : "bg-amber-400"} />
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* ── 10. Concept diversity ── */}
      <Section title="Concept Diversity">
        <Gauge label="Diversity score" pct={div?.diversity_score_pct ?? 0} color="text-blue-400" />
        <Row label="Avg product overlap" value={String(div?.avg_product_overlap ?? 0)} />
        <Row label="Avg tag overlap"     value={String(div?.avg_tag_overlap ?? 0)} />
        <div className="flex justify-end">
          <Badge text={div?.diversity_target_met ? "✓ Diverse" : "⚠ Overlap"} variant={div?.diversity_target_met ? "success" : "warn"} />
        </div>
        {div?.pairwise_overlaps?.map(p => (
          <div key={p.pair} className="pl-2 border-l border-slate-700 space-y-0.5">
            <div className="text-slate-500 text-xs truncate">{p.pair}</div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Overlap</span>
              <div className="flex items-center gap-1">
                <Badge text={p.diverse ? "diverse" : "similar"} variant={p.diverse ? "success" : "warn"} />
                <span className="font-mono text-slate-300">{p.overlap_pct}%</span>
              </div>
            </div>
          </div>
        ))}
      </Section>

      {/* ── 11. Error rate / pipeline health ── */}
      <Section title="Error Rate + Pipeline Health">
        <Gauge label="Handoff success" pct={ph?.handoff_success_pct ?? 0} color="text-teal-400" />
        <Row label="Status"          value="" />
        <div className="flex justify-end">
          <Badge
            text={ph?.status ?? "—"}
            variant={ph?.status === "success" ? "success" : ph?.status === "partial" ? "warn" : "error"}
          />
        </div>
        <Row label="Agents completed" value={`${ph?.agents_succeeded ?? 0} / ${(ph?.agents_succeeded ?? 0) + (ph?.agents_failed ?? 0)}`} />
        <Row label="Error count"      value={String(ph?.error_count ?? 0)} />
        <Row label="Warning count"    value={String(ph?.warning_count ?? 0)} />
        <Row label="Error rate"       value={`${ph?.error_rate_pct ?? 0}%`} />
        {ph?.handoffs && Object.entries(ph.handoffs).map(([k, v]) => (
          <div key={k} className="flex justify-between text-xs">
            <span className="text-slate-500">{k.replace(/_/g, " ")}</span>
            <Badge text={v ? "✓" : "✗"} variant={v ? "success" : "error"} />
          </div>
        ))}
        {ph?.errors_by_agent && Object.keys(ph.errors_by_agent).length > 0 && (
          <div className="space-y-1 pt-1">
            <div className="text-slate-500">Errors by agent</div>
            {Object.entries(ph.errors_by_agent).map(([agent, info]) => (
              <div key={agent} className="pl-2 border-l border-red-400/40 space-y-0.5">
                <div className="text-red-400 capitalize">{agent}</div>
                <Row label="Errors"   value={String(info.errors)} />
                <Row label="Warnings" value={String(info.warnings)} />
              </div>
            ))}
          </div>
        )}
      </Section>

    </div>
  )
}