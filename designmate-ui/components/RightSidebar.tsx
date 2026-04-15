// components/RightSidebar.tsx
"use client"

import { useEffect, useRef, useState } from "react"
import { useStore } from "@/lib/store"
import { createSSEConnection, refineDesign, getMetrics } from "@/lib/api"
import { AgentLog } from "@/lib/types"
import { motion, AnimatePresence } from "framer-motion"
import { Terminal, Send, Loader2, BarChart2 } from "lucide-react"
import MetricsDashboard from "./MetricsDashboard"

const LEVEL_STYLES: Record<string, string> = {
  info:    "text-slate-300",
  success: "text-emerald-400",
  warning: "text-amber-400",
  error:   "text-red-400",
}
const LEVEL_PREFIX: Record<string, string> = {
  info: "›", success: "✓", warning: "⚠", error: "✗",
}
const AGENT_COLORS: Record<string, string> = {
  vision: "text-blue-400", planning: "text-purple-400",
  optimization: "text-teal-400", retrieval: "text-amber-400",
  rendering: "text-pink-400", dialogue: "text-slate-400",
}

function LogEntry({ log }: { log: AgentLog }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.15 }}
      className="flex gap-2 py-0.5 font-mono text-xs leading-relaxed"
    >
      <span className={`${LEVEL_STYLES[log.level] ?? "text-slate-300"} flex-shrink-0 w-3`}>
        {LEVEL_PREFIX[log.level] ?? "›"}
      </span>
      <span className={`${AGENT_COLORS[log.agent] ?? "text-slate-400"} flex-shrink-0 uppercase text-xs`}>
        [{log.agent}]
      </span>
      <span className={LEVEL_STYLES[log.level] ?? "text-slate-300"}>{log.message}</span>
    </motion.div>
  )
}

export default function RightSidebar() {
  const {
    sessionId, agentLogs, appendLog,
    metrics, isRefining, setRefining,
    refineMessage, setRefineMessage,
    applyRefineResponse, applyPartialUpdate, setError,
  } = useStore()

  const logsEndRef                      = useRef<HTMLDivElement>(null)
  const [sseConnected, setSseConnected] = useState(false)
  const [tab, setTab]                   = useState<"logs" | "metrics">("logs")

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [agentLogs])

  useEffect(() => {
    if (!sessionId || sseConnected) return
    setSseConnected(true)
    const es = createSSEConnection(
      sessionId,
      (log) => {
        const l = log as AgentLog
        appendLog(l)
        if (l.event === "search_complete") {
          getMetrics(sessionId).then(m => applyPartialUpdate({ metrics: m })).catch(() => {})
        }
      },
      () => setSseConnected(false)
    )
    return () => { es.close(); setSseConnected(false) }
  }, [sessionId])

  const handleRefine = async () => {
    if (!sessionId || !refineMessage.trim()) return
    setRefining(true)
    try {
      applyRefineResponse(await refineDesign(sessionId, refineMessage))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Refinement failed")
      setRefining(false)
    }
  }

  // Switch to metrics tab automatically when metrics arrive
  useEffect(() => {
    if (metrics) setTab("metrics")
  }, [!!metrics])

  return (
    <div className="w-80 min-w-80 h-full bg-slate-900 border-l border-slate-700/50 flex flex-col">

      {/* Header */}
      <div className="p-4 border-b border-slate-700/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Agent Panel
          </span>
          {sseConnected && (
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400">live</span>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1">
          <button
            onClick={() => setTab("logs")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors ${
              tab === "logs"
                ? "bg-slate-700 text-white"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            <Terminal size={11} />
            Logs
            <span className="text-slate-500 font-mono">{agentLogs.length}</span>
          </button>
          <button
            onClick={() => setTab("metrics")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors ${
              tab === "metrics"
                ? "bg-slate-700 text-white"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            <BarChart2 size={11} />
            Metrics
            {metrics && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {tab === "logs" && (
          <div className="p-3 space-y-0.5 bg-slate-950/50 font-mono min-h-full">
            {agentLogs.length === 0 ? (
              <div className="flex items-center justify-center h-40">
                <p className="text-xs text-slate-600">Waiting for agent activity...</p>
              </div>
            ) : (
              <AnimatePresence initial={false}>
                {agentLogs.map((log, i) => <LogEntry key={i} log={log} />)}
              </AnimatePresence>
            )}
            <div ref={logsEndRef} />
          </div>
        )}

        {tab === "metrics" && (
          metrics
            ? <MetricsDashboard metrics={metrics} />
            : (
              <div className="flex items-center justify-center h-40">
                <p className="text-xs text-slate-600">Run an analysis to see metrics</p>
              </div>
            )
        )}
      </div>

      {/* Refine input */}
      {sessionId && (
        <div className="p-3 border-t border-slate-700/50">
          <div className="flex gap-2">
            <input
              type="text"
              value={refineMessage}
              onChange={e => setRefineMessage(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleRefine()}
              placeholder="e.g. make it more rustic..."
              disabled={isRefining}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg
                         px-3 py-2 text-xs text-white placeholder-slate-500
                         outline-none focus:border-purple-500 disabled:opacity-50"
            />
            <motion.button
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={handleRefine}
              disabled={isRefining || !refineMessage.trim()}
              className="p-2 rounded-lg bg-purple-600 hover:bg-purple-500
                         disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {isRefining
                ? <Loader2 size={14} className="text-white animate-spin" />
                : <Send size={14} className="text-white" />
              }
            </motion.button>
          </div>
        </div>
      )}
    </div>
  )
}