// components/RoomScene.tsx
"use client"

import { useRef } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Box, Grid, Text, Environment } from "@react-three/drei"
import { useStore } from "@/lib/store"
import { SourcedProduct } from "@/lib/types"
import * as THREE from "three"

const CATEGORY_COLORS: Record<string, string> = {
  sofa:          "#a855f7",
  coffee_table:  "#3b82f6",
  rug:           "#10b981",
  floor_lamp:    "#f59e0b",
  accent_chair:  "#ef4444",
  throw_blanket: "#ec4899",
  bookshelf:     "#8b5cf6",
  default:       "#64748b",
}

function FurnitureBox({
  product,
  index,
  total,
  isSelected,
  onClick,
  roomWidth,
  roomLength,
}: {
  product: SourcedProduct
  index: number
  total: number
  isSelected: boolean
  onClick: () => void
  roomWidth: number
  roomLength: number
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const color = CATEGORY_COLORS[product.category] ?? CATEGORY_COLORS.default

  const w = Math.max((product.dimensions.width / 12) * 0.9, 0.3)
  const d = Math.max((product.dimensions.depth / 12) * 0.9, 0.3)
  const h = Math.max((product.dimensions.height / 12) * 0.9, 0.15)

  // Distribute items in a grid pattern within room bounds
  const cols    = Math.ceil(Math.sqrt(total))
  const row     = Math.floor(index / cols)
  const col     = index % cols
  const spacing = Math.min(roomWidth, roomLength) / (cols + 1)
  const x = (col - (cols - 1) / 2) * spacing
  const z = (row - Math.floor(total / cols) / 2) * spacing
  const y = h / 2

  return (
    <group position={[x, y, z]} onClick={onClick}>
      <Box ref={meshRef} args={[w, h, d]}>
        <meshStandardMaterial
          color={color}
          wireframe={!isSelected}
          opacity={isSelected ? 0.7 : 1}
          transparent={isSelected}
          emissive={isSelected ? color : "#000000"}
          emissiveIntensity={isSelected ? 0.3 : 0}
        />
      </Box>
      {isSelected && (
        <Box args={[w + 0.08, h + 0.08, d + 0.08]}>
          <meshBasicMaterial
            color="white"
            wireframe
            opacity={0.4}
            transparent
          />
        </Box>
      )}
      <Text
        position={[0, h / 2 + 0.2, 0]}
        fontSize={0.2}
        color={color}
        anchorX="center"
        anchorY="bottom"
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        {product.category.replace(/_/g, " ")}
      </Text>
      <Text
        position={[0, h / 2 + 0.45, 0]}
        fontSize={0.15}
        color="#94a3b8"
        anchorX="center"
        anchorY="bottom"
      >
        ${product.price}
      </Text>
    </group>
  )
}

function RoomBoundary({
  roomWidth,
  roomLength,
}: {
  roomWidth: number
  roomLength: number
}) {
  return (
    <>
      <Grid
        args={[roomWidth, roomLength]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#1e293b"
        sectionSize={3}
        sectionThickness={1}
        sectionColor="#334155"
        fadeDistance={50}
        fadeStrength={1}
        infiniteGrid={false}
      />
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        receiveShadow
      >
        <planeGeometry args={[roomWidth, roomLength]} />
        <meshStandardMaterial
          color="#0f172a"
          opacity={0.9}
          transparent
        />
      </mesh>
      {/* Room boundary walls — wireframe */}
      <lineSegments>
        <edgesGeometry
          args={[new THREE.BoxGeometry(roomWidth, 3, roomLength)]}
        />
        <lineBasicMaterial color="#334155" opacity={0.4} transparent />
      </lineSegments>
    </>
  )
}

function SceneContent() {
  const {
    sourcedProducts,
    selectedConceptIndex,
    selectedProductId,
    setSelectedProduct,
    analyzeResponse,
  } = useStore()

  const concept      = sourcedProducts[selectedConceptIndex]
  const items        = concept?.items ?? []
  const roomAnalysis = analyzeResponse?.room_analysis
  const roomWidth    = roomAnalysis?.dimensions.width_ft  ?? 12
  const roomLength   = roomAnalysis?.dimensions.length_ft ?? 14

  return (
    <>
      <ambientLight intensity={0.4} />
      <pointLight
        position={[roomWidth / 2, 6, roomLength / 2]}
        intensity={1.2}
        color="#c4b5fd"
        castShadow
      />
      <pointLight
        position={[-roomWidth / 2, 4, -roomLength / 2]}
        intensity={0.6}
        color="#60a5fa"
      />

      <RoomBoundary roomWidth={roomWidth} roomLength={roomLength} />

      {items.map((product, index) => (
        <FurnitureBox
          key={`${product.product_id}-${selectedConceptIndex}`}
          product={product}
          index={index}
          total={items.length}
          roomWidth={roomWidth}
          roomLength={roomLength}
          isSelected={selectedProductId === product.product_id}
          onClick={() =>
            setSelectedProduct(
              selectedProductId === product.product_id
                ? null
                : product.product_id
            )
          }
        />
      ))}

      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        minDistance={2}
        maxDistance={30}
        maxPolarAngle={Math.PI / 2.1}
        makeDefault
      />
    </>
  )
}

export default function RoomScene() {
  const { sourcedProducts, selectedConceptIndex, analyzeResponse } = useStore()
  const concept   = sourcedProducts[selectedConceptIndex]
  const items     = concept?.items ?? []
  const roomWidth = analyzeResponse?.room_analysis?.dimensions.width_ft  ?? 12
  const roomLen   = analyzeResponse?.room_analysis?.dimensions.length_ft ?? 14
  const camDist   = Math.max(roomWidth, roomLen) * 0.9

  if (items.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center
                      bg-slate-950">
        <p className="text-slate-500 text-sm">
          No products to display in 3D view
        </p>
      </div>
    )
  }

  return (
    <div className="w-full h-full bg-slate-950">
      <Canvas
        key={`canvas-${selectedConceptIndex}`}
        camera={{
          position: [camDist, camDist * 0.8, camDist],
          fov: 50,
          near: 0.1,
          far: 200
        }}
        shadows
        style={{ background: "#020617" }}
        gl={{ antialias: true }}
      >
        <SceneContent />
      </Canvas>
    </div>
  )
}