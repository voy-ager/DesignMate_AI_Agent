// app/page.tsx
"use client"

import { useStore } from "@/lib/store"
import LeftSidebar from "@/components/LeftSidebar"
import CenterCanvas from "@/components/CenterCanvas"
import RightSidebar from "@/components/RightSidebar"
import BudgetMeter from "@/components/BudgetMeter"
import ProductTray from "@/components/ProductTray"
import { AnimatePresence, motion } from "framer-motion"

export default function Home() {
  const { error, setError } = useStore()

  return (
    <div className="h-screen w-screen bg-slate-950 text-white flex flex-col
                    overflow-hidden">

      <BudgetMeter />

      <div className="flex-1 flex overflow-hidden">
        <LeftSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <CenterCanvas />
          <ProductTray />
        </div>
        <RightSidebar />
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50
                       bg-red-950 border border-red-500/50 rounded-xl
                       px-4 py-3 flex items-center gap-3 shadow-xl"
          >
            <span className="text-red-400 text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300 text-xs underline"
            >
              Dismiss
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}