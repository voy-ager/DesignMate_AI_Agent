// components/RightSidebar.tsx
"use client"

import { useEffect, useRef, useState } from "react"
import { useStore } from "@/lib/store"
import { createSSEConnection, refineDesign, getMetrics } from "@/lib/api"
import { AgentLog } from "@/lib/types"
import { motion, AnimatePresence } from "framer-motion"
import { Terminal, Send, Loader2, TrendingUp } from "lucide-react"

const LEVEL_STYLES: Record<string, string> = {
  info:    "text-slate-300",
  success: "text-emerald-400",
  warning: "text-amber-400",
  error:   "text-red-400",
}

const LEVEL_PREFIX: Record<string, string> = {
  info:    "›",
  success: "✓",
  warning: "⚠",
  error:   "✗",
}

const AGENT_COLORS: Record<string, string> = {
  vision:       "text-blue-400",
  planning:     "text-purple-400",
  optimization: "text-teal-400",
  retrieval:    "text-amber-400",
  rendering:    "text-pink-400",
  dialogue:     "text-slate-400",
}

function LogEntry({ log }: { log: AgentLog }) {
  const levelStyle  = LEVEL_STYLES[log.level]  ?? "text-slate-300"
  const prefix      = LEVEL_PREFIX[log.level]  ?? "›"
  const agentColor  = AGENT_COLORS[log.agent]  ?? "text-slate-400"

  return (
    <motion.div
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.15 }}
      className="flex gap-2 py-0.5 font-mono text-xs leading-relaxed"
    >
      <span className={`${levelStyle} flex-shrink-0 w-3`}>{prefix}</span>
      <span className={`${agentColor} flex-shrink-0 uppercase text-xs`}>
        [{log.agent}]
      </span>
      <span className={levelStyle}>{log.message}</span>
    </motion.div>
  )
}

function ConfidenceGauge({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  const pct = Math.round(value * 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className={color}>{pct}%</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${
            pct >= 75 ? "bg-emerald-400" :
            pct >= 50 ? "bg-amber-400" : "bg-red-400"
          }`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  )
}

export default function RightSidebar() {
  const {
    sessionId, agentLogs, appendLog,
    metrics, isRefining, setRefining,
    refineMessage, setRefineMessage,
    applyRefineResponse, applyPartialUpdate, setError,
  } = useStore()

  const logsEndRef                    = useRef<HTMLDivElement>(null)
  const [sseConnected, setSseConnected] = useState(false)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [agentLogs])

  useEffect(() => {
    if (!sessionId || sseConnected) return
    setSseConnected(true)

    const eventSource = createSSEConnection(
      sessionId,
      (log) => {
        const logEntry = log as AgentLog
        appendLog(logEntry)

        // Priority 4: as soon as retrieval completes fetch fresh metrics
        // This makes product cards appear before rendering finishes
        if (logEntry.event === "search_complete") {
          getMetrics(sessionId)
            .then((m) => applyPartialUpdate({ metrics: m }))
            .catch(() => {})
        }
      },
      () => setSseConnected(false)
    )

    return () => {
      eventSource.close()
      setSseConnected(false)
    }
  }, [sessionId])

  const handleRefine = async () => {
    if (!sessionId || !refineMessage.trim()) return
    setRefining(true)
    try {
      const response = await refineDesign(sessionId, refineMessage)
      applyRefineResponse(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Refinement failed")
      setRefining(false)
    }
  }

  return (
    <div className="w-80 min-w-80 h-full bg-slate-900 border-l
                    border-slate-700/50 flex flex-col">

      <div className="p-4 border-b border-slate-700/50">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Terminal size={14} className="text-emerald-400" />
            <span className="text-xs font-semibold text-slate-300
                             uppercase tracking-wider">
              Agent Thought Trace
            </span>
          </div>
          {sseConnected && (
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400
                              animate-pulse" />
              <span className="text-xs text-emerald-400">live</span>
            </div>
          )}
        </div>
        <p className="text-xs text-slate-500">
          {agentLogs.length} events logged
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-0.5
                      bg-slate-950/50 font-mono">
        {agentLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-xs text-slate-600">
              Waiting for agent activity...
            </p>
          </div>
        ) : (
          <>
            <AnimatePresence initial={false}>
              {agentLogs.map((log, i) => (
                <LogEntry key={i} log={log} />
              ))}
            </AnimatePresence>
            <div ref={logsEndRef} />
          </>
        )}
      </div>

      {metrics && (
        <div className="p-4 border-t border-slate-700/50 space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={12} className="text-purple-400" />
            <span className="text-xs font-semibold text-slate-300
                             uppercase tracking-wider">
              Confidence Scores
            </span>
          </div>
          <ConfidenceGauge
            label="Budget accuracy"
            value={metrics.budget_accuracy}
            color="text-emerald-400"
          />
          <ConfidenceGauge
            label="Style coherence"
            value={metrics.style_coherence_avg}
            color="text-purple-400"
          />
          <ConfidenceGauge
            label="Constraint satisfaction"
            value={metrics.constraint_satisfaction_rate}
            color="text-blue-400"
          />
          <div className="flex justify-between text-xs pt-1
                          border-t border-slate-700/50">
            <span className="text-slate-500">Total latency</span>
            <span className="text-slate-300 font-mono">
              {metrics.total_latency_seconds.toFixed(3)}s
            </span>
          </div>
        </div>
      )}

      {sessionId && (
        <div className="p-3 border-t border-slate-700/50">
          <div className="flex gap-2">
            <input
              type="text"
              value={refineMessage}
              onChange={(e) => setRefineMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleRefine()}
              placeholder="e.g. make it more rustic..."
              disabled={isRefining}
              className="flex-1 bg-slate-800 border border-slate-700
                         rounded-lg px-3 py-2 text-xs text-white
                         placeholder-slate-500 outline-none
                         focus:border-purple-500 disabled:opacity-50"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleRefine}
              disabled={isRefining || !refineMessage.trim()}
              className="p-2 rounded-lg bg-purple-600 hover:bg-purple-500
                         disabled:opacity-40 disabled:cursor-not-allowed
                         transition-colors"
            >
              {isRefining ? (
                <Loader2 size={14} className="text-white animate-spin" />
              ) : (
                <Send size={14} className="text-white" />
              )}
            </motion.button>
          </div>
        </div>
      )}
    </div>
  )
}