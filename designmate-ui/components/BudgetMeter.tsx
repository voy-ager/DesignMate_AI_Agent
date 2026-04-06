// components/BudgetMeter.tsx
"use client"

import { useStore } from "@/lib/store"
import { Progress } from "@/components/ui/progress"
import { motion, AnimatePresence } from "framer-motion"

export default function BudgetMeter() {
  const { budget, sourcedProducts, selectedConceptIndex, metrics } = useStore()

  const selectedConcept = sourcedProducts[selectedConceptIndex]
  const totalCost = selectedConcept?.total_cost ?? 0
  const budgetRemaining = selectedConcept?.budget_remaining ?? budget
  const percentage = Math.min((totalCost / budget) * 100, 100)
  const isOverBudget = budgetRemaining < 0
  const isNearLimit = percentage >= 85 && !isOverBudget

  return (
    <div className="flex items-center gap-4 px-6 py-3 border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm">

      <div className="flex items-center gap-2 min-w-fit">
        <span className="text-xs text-slate-400 font-medium">BUDGET</span>
        <span className="text-xs font-mono text-white">
          ${budget.toLocaleString()}
        </span>
      </div>

      <div className="flex-1 relative">
        <Progress
          value={percentage}
          className={`h-2 ${isOverBudget ? "bg-red-950" : "bg-slate-700"}`}
        />
        <motion.div
          className={`absolute inset-0 rounded-full h-2 origin-left ${
            isOverBudget
              ? "bg-red-500"
              : isNearLimit
              ? "bg-amber-400"
              : "bg-emerald-400"
          }`}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: percentage / 100 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>

      <div className="flex items-center gap-3 min-w-fit">
        <div className="text-right">
          <div className="text-xs text-slate-400">Spent</div>
          <div className="text-xs font-mono text-white">
            ${totalCost.toLocaleString()}
          </div>
        </div>

        <div className="w-px h-6 bg-slate-700" />

        <AnimatePresence mode="wait">
          <motion.div
            key={budgetRemaining}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            className="text-right"
          >
            <div className="text-xs text-slate-400">Remaining</div>
            <div className={`text-xs font-mono font-medium ${
              isOverBudget ? "text-red-400" : "text-emerald-400"
            }`}>
              {isOverBudget ? "-" : ""}$
              {Math.abs(budgetRemaining).toLocaleString()}
            </div>
          </motion.div>
        </AnimatePresence>

        {isOverBudget && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="px-2 py-1 rounded bg-red-500/20 border border-red-500/50"
          >
            <span className="text-xs text-red-400 font-medium">
              LIMIT EXCEEDED
            </span>
          </motion.div>
        )}

        {metrics && (
          <div className="text-right border-l border-slate-700 pl-3">
            <div className="text-xs text-slate-400">Coherence</div>
            <div className="text-xs font-mono text-purple-400">
              {(metrics.style_coherence_avg * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>
    </div>
  )
}