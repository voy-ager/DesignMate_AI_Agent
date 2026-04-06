// components/LeftSidebar.tsx
"use client"

import { useCallback, useState } from "react"
import { useStore } from "@/lib/store"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { analyzeRoom } from "@/lib/api"
import StyleGrid from "./StyleGrid"
import { motion } from "framer-motion"
import { Upload, Loader2, Zap } from "lucide-react"

export default function LeftSidebar() {
  const {
    budget, setBudget,
    style,
    imageFile, imagePreview, setImageFile,
    isLoading, setLoading,
    setError, setAnalyzeResponse,
  } = useStore()

  const [hardLimit, setHardLimit] = useState(true)
  const [isDragging, setIsDragging] = useState(false)

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return
    const preview = URL.createObjectURL(file)
    setImageFile(file, preview)
  }, [setImageFile])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleAnalyze = async () => {
    if (!imageFile) {
      setError("Please upload a room image first")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await analyzeRoom(imageFile, budget, style)
      setAnalyzeResponse(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-72 min-w-72 h-full bg-slate-900 border-r border-slate-700/50
                    flex flex-col overflow-y-auto">

      <div className="p-4 border-b border-slate-700/50">
        <div className="flex items-center gap-2 mb-1">
          <Zap size={14} className="text-purple-400" />
          <span className="text-xs font-semibold text-slate-300 tracking-widest uppercase">
            DesignMate AI
          </span>
        </div>
        <p className="text-xs text-slate-500">
          Autonomous interior design agent
        </p>
      </div>

      <div className="p-4 border-b border-slate-700/50 space-y-4">
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-slate-300 uppercase tracking-wider">
              Budget
            </span>
            <span className="text-sm font-mono text-white">
              ${budget.toLocaleString()}
            </span>
          </div>
          <Slider
            min={500}
            max={10000}
            step={100}
            value={[budget]}
            onValueChange={([val]) => setBudget(val)}
            className="mb-3"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">Hard limit</span>
            <Switch
              checked={hardLimit}
              onCheckedChange={setHardLimit}
            />
          </div>
          {hardLimit && (
            <p className="text-xs text-amber-400/70 mt-1">
              Agent will not exceed ${budget.toLocaleString()}
            </p>
          )}
        </div>
      </div>

      <div className="p-4 border-b border-slate-700/50">
        <span className="text-xs font-medium text-slate-300 uppercase tracking-wider block mb-3">
          Room Photo
        </span>

        <motion.div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById("file-input")?.click()}
          animate={{ borderColor: isDragging ? "#a855f7" : "#334155" }}
          className="border-2 border-dashed border-slate-700 rounded-lg p-4
                     cursor-pointer hover:border-slate-500 transition-colors
                     flex flex-col items-center justify-center min-h-32 relative"
        >
          {imagePreview ? (
            <img
              src={imagePreview}
              alt="Room preview"
              className="w-full h-32 object-cover rounded-md"
            />
          ) : (
            <>
              <Upload size={20} className="text-slate-500 mb-2" />
              <span className="text-xs text-slate-500 text-center">
                Drop room photo here or click to upload
              </span>
            </>
          )}
          <input
            id="file-input"
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFile(file)
            }}
          />
        </motion.div>
      </div>

      <div className="p-4 border-b border-slate-700/50">
        <span className="text-xs font-medium text-slate-300 uppercase tracking-wider block mb-3">
          Style DNA
        </span>
        <StyleGrid />
      </div>

      <div className="p-4 mt-auto">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleAnalyze}
          disabled={isLoading || !imageFile}
          className="w-full py-3 rounded-lg bg-purple-600 hover:bg-purple-500
                     disabled:opacity-40 disabled:cursor-not-allowed
                     text-white text-sm font-medium transition-colors
                     flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              Analyzing room...
            </>
          ) : (
            <>
              <Zap size={14} />
              Generate Designs
            </>
          )}
        </motion.button>
      </div>
    </div>
  )
}