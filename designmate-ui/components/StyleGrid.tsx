// components/StyleGrid.tsx
"use client"

import { useStore } from "@/lib/store"
import { StyleMood } from "@/lib/types"
import { motion } from "framer-motion"

const MOODS: Array<{
  id: StyleMood
  label: string
  description: string
  emoji: string
}> = [
  { id: "modern", label: "Modern", description: "Clean lines, neutral tones", emoji: "◼" },
  { id: "minimalist", label: "Minimalist", description: "Less is more", emoji: "○" },
  { id: "scandinavian", label: "Scandinavian", description: "Warm, hygge vibes", emoji: "❄" },
  { id: "industrial", label: "Industrial", description: "Raw metals, exposed brick", emoji: "⚙" },
  { id: "contemporary", label: "Contemporary", description: "Bold statement pieces", emoji: "◆" },
  { id: "rustic", label: "Rustic", description: "Natural wood, earthy tones", emoji: "🌿" },
  { id: "bohemian", label: "Bohemian", description: "Eclectic, layered textures", emoji: "✦" },
  { id: "mid-century", label: "Mid-Century", description: "Retro modern classics", emoji: "◉" },
]

export default function StyleGrid() {
  const { style, setStyle } = useStore()

  return (
    <div className="grid grid-cols-2 gap-2">
      {MOODS.map((mood) => {
        const isSelected = style === mood.id
        return (
          <motion.button
            key={mood.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setStyle(mood.id)}
            className={`
              p-3 rounded-lg border text-left transition-all duration-200
              ${isSelected
                ? "border-white bg-white/10 text-white"
                : "border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-500 hover:text-slate-200"
              }
            `}
          >
            <div className="text-lg mb-1">{mood.emoji}</div>
            <div className="text-xs font-medium">{mood.label}</div>
            <div className="text-xs opacity-60 mt-0.5 leading-tight">
              {mood.description}
            </div>
          </motion.button>
        )
      })}
    </div>
  )
}