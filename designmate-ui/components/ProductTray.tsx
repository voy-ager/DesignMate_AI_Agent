// components/ProductTray.tsx
"use client"

import React from "react"
import { useStore } from "@/lib/store"
import { Badge } from "@/components/ui/badge"
import { motion, AnimatePresence } from "framer-motion"
import { ExternalLink, CheckCircle, AlertCircle } from "lucide-react"
import { SourcedProduct } from "@/lib/types"

function SkeletonCard() {
  return (
    <div className="flex-shrink-0 w-52 p-3 rounded-xl border border-slate-700 bg-slate-800/80 overflow-hidden relative">
      <div className="h-3 bg-slate-700 rounded mb-3 w-4/5" />
      <div className="h-3 bg-slate-700 rounded mb-4 w-3/5" />
      <div className="h-2 bg-slate-700 rounded mb-2 w-full" />
      <div className="h-1.5 bg-slate-700 rounded mb-4 w-full" />
      <div className="flex justify-between">
        <div className="h-5 bg-slate-700 rounded w-20" />
        <div className="h-5 bg-slate-700 rounded w-10" />
      </div>
      <motion.div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(90deg, transparent, rgba(148,163,184,0.08), transparent)",
        }}
        initial={{ x: "-100%" }}
        animate={{ x: "100%" }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
      />
    </div>
  )
}

function BuyLink({ url }: { url: string }) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.stopPropagation()
  }
  return React.createElement(
    "a",
    {
      href: url,
      target: "_blank",
      rel: "noopener noreferrer",
      onClick: handleClick,
      className: "flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors",
    },
    "Buy ",
    React.createElement(ExternalLink, { size: 10 })
  )
}

function ProductCard({
  product,
  isSelected,
  onClick,
}: {
  product: SourcedProduct
  isSelected: boolean
  onClick: () => void
}) {
  const matchPct = Math.round(product.similarity_score * 100)
  const borderClass = isSelected
    ? "border-purple-500 bg-purple-950/30"
    : "border-slate-700 hover:border-slate-500"

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={"flex-shrink-0 w-52 p-3 rounded-xl border cursor-pointer transition-all duration-200 bg-slate-800/80 " + borderClass}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs font-medium text-white leading-tight line-clamp-2">
          {product.name}
        </span>
        {product.within_budget ? (
          <CheckCircle size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />
        ) : (
          <AlertCircle size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
        )}
      </div>

      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-mono font-medium text-white">
          ${product.price.toLocaleString()}
        </span>
        <Badge
          className={"text-xs " + (product.within_budget
            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
            : "bg-amber-500/20 text-amber-400 border-amber-500/30")}
        >
          {product.within_budget ? "In budget" : "Over budget"}
        </Badge>
      </div>

      <div className="space-y-1 mb-3">
        <div className="flex justify-between text-xs">
          <span className="text-slate-400">Match score</span>
          <span className="text-purple-400 font-mono">{matchPct}%</span>
        </div>
        <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-purple-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: matchPct + "%" }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <Badge className="bg-slate-700 text-slate-300 border-slate-600 text-xs">
          {product.category.replace(/_/g, " ")}
        </Badge>
        <BuyLink url={product.purchase_url} />
      </div>
    </motion.div>
  )
}

export default function ProductTray() {
  const {
    sourcedProducts,
    selectedConceptIndex,
    selectedProductId,
    setSelectedProduct,
    isLoading,
  } = useStore()

  const concept = sourcedProducts[selectedConceptIndex]
  const items = concept?.items ?? []

  if (!concept || items.length === 0) {
    if (isLoading) {
      return (
        <div className="border-t border-slate-700/50 bg-slate-900/80 backdrop-blur-sm px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Product Manifest
            </span>
            <span className="text-xs text-slate-500 animate-pulse">
              Agents sourcing products...
            </span>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="border-t border-slate-700/50 bg-slate-900/80 backdrop-blur-sm px-4 py-3">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Product Manifest
        </span>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>{items.length} items</span>
          <span className="text-slate-600">|</span>
          <span>
            Total:{" "}
            <span className="text-white font-mono">
              ${concept.total_cost.toLocaleString()}
            </span>
          </span>
          <span className={concept.budget_remaining >= 0 ? "text-emerald-400" : "text-red-400"}>
            {concept.budget_remaining >= 0 ? "+" : ""}${concept.budget_remaining.toLocaleString()} remaining
          </span>
        </div>
      </div>

      <AnimatePresence>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {items.map((product, i) => (
            <motion.div
              key={product.product_id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.3 }}
            >
              <ProductCard
                product={product}
                isSelected={selectedProductId === product.product_id}
                onClick={() =>
                  setSelectedProduct(
                    selectedProductId === product.product_id
                      ? null
                      : product.product_id
                  )
                }
              />
            </motion.div>
          ))}
        </div>
      </AnimatePresence>
    </div>
  )
}