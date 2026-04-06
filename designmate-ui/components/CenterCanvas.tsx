// components/CenterCanvas.tsx
"use client"

import { Suspense, useState, useEffect } from "react"
import { useStore } from "@/lib/store"
import { Badge } from "@/components/ui/badge"
import { motion } from "framer-motion"
import { Eye, Box, Loader2 } from "lucide-react"
import dynamic from "next/dynamic"

const RoomScene = dynamic(() => import("./RoomScene"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-950">
      <Loader2 className="animate-spin text-purple-400" size={32} />
    </div>
  ),
})

export default function CenterCanvas() {
  const {
    renderUrls,
    sourcedProducts,
    selectedConceptIndex,
    setSelectedConcept,
    viewMode,
    setViewMode,
    isLoading,
    analyzeResponse,
  } = useStore()

  const [sceneKey, setSceneKey] = useState(0)

  useEffect(() => {
    if (viewMode === "blueprint") {
      setSceneKey((k) => k + 1)
    }
  }, [viewMode, selectedConceptIndex])

  const concepts        = analyzeResponse?.design_concepts ?? []
  const selectedRender  = renderUrls[selectedConceptIndex]
  const selectedConcept = sourcedProducts[selectedConceptIndex]
  const hasResults      = renderUrls.length > 0

  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden">

      <div className="flex items-center justify-between px-4 py-3
                      border-b border-slate-700/50 bg-slate-900/50">
        <div className="flex gap-2">
          {concepts.map((concept, i) => (
            <motion.button
              key={i}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedConcept(i)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                selectedConceptIndex === i
                  ? "bg-purple-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
              }`}
            >
              {concept.concept_name}
            </motion.button>
          ))}
        </div>

        {hasResults && (
          <div className="flex items-center gap-2 bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode("render")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md
                          text-xs font-medium transition-all ${
                viewMode === "render"
                  ? "bg-slate-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Eye size={12} />
              Photorealistic
            </button>
            <button
              onClick={() => setViewMode("blueprint")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md
                          text-xs font-medium transition-all ${
                viewMode === "blueprint"
                  ? "bg-slate-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Box size={12} />
              3D Blueprint
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 relative overflow-hidden">

        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center
                          justify-center gap-4 bg-slate-950 z-20">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Loader2 size={40} className="text-purple-400" />
            </motion.div>
            <div className="text-sm text-slate-400">
              Agents are designing your room...
            </div>
          </div>
        )}

        {!isLoading && !hasResults && (
          <div className="absolute inset-0 flex flex-col items-center
                          justify-center gap-4 bg-slate-950 z-10">
            <div className="w-24 h-24 rounded-2xl bg-slate-800 border
                            border-slate-700 flex items-center justify-center">
              <Box size={36} className="text-slate-600" />
            </div>
            <div className="text-center">
              <p className="text-slate-300 font-medium">No design yet</p>
              <p className="text-slate-500 text-sm mt-1">
                Upload a room photo and click Generate
              </p>
            </div>
          </div>
        )}

        {hasResults && (
          <>
            {/* Photorealistic view — hidden with CSS not unmounted */}
            <div
              className="absolute inset-0 transition-opacity duration-300"
              style={{ opacity: viewMode === "render" ? 1 : 0,
                       pointerEvents: viewMode === "render" ? "auto" : "none" }}
            >
              {selectedRender && (
                <img
                  src={selectedRender.image_url}
                  alt={selectedRender.concept_name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    target.src = "https://placehold.co/1024x1024/1e293b/64748b?text=Render+unavailable"
                  }}
                />
              )}
              {selectedConcept && (
                <div className="absolute bottom-4 left-4 right-4 flex
                                items-center justify-between">
                  <div className="flex gap-2 flex-wrap">
                    {selectedConcept.style_tags.map((tag) => (
                      <Badge
                        key={tag}
                        className="bg-black/60 text-white border-white/20
                                   backdrop-blur-sm text-xs"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <Badge className="bg-black/60 text-emerald-400
                                   border-emerald-400/30 backdrop-blur-sm">
                    ${selectedConcept.total_cost.toLocaleString()} total
                  </Badge>
                </div>
              )}
            </div>

            {/* Blueprint view — hidden with CSS not unmounted */}
            <div
              className="absolute inset-0 transition-opacity duration-300"
              style={{ opacity: viewMode === "blueprint" ? 1 : 0,
                       pointerEvents: viewMode === "blueprint" ? "auto" : "none" }}
            >
              <Suspense
                key={`scene-${sceneKey}`}
                fallback={
                  <div className="w-full h-full flex items-center
                                  justify-center bg-slate-950">
                    <Loader2 className="animate-spin text-purple-400"
                             size={32} />
                  </div>
                }
              >
                <RoomScene key={`room-${sceneKey}`} />
              </Suspense>
              <div className="absolute top-4 left-4 bg-black/60
                              backdrop-blur-sm rounded-lg px-3 py-2
                              pointer-events-none">
                <p className="text-xs text-slate-400">
                  OR-Tools bounding boxes
                </p>
                <p className="text-xs text-purple-400 font-medium">
                  Orbit • Zoom • Pan
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}