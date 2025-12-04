import { useRef, Suspense, useState, useEffect } from 'react'
import { Canvas, useFrame, useLoader } from '@react-three/fiber'
import { OrbitControls, Environment, ContactShadows, Html } from '@react-three/drei'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader'
import * as THREE from 'three'

// Component to load and display the pump model
function PumpModel({ faultState, sensorData }) {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)
  
  // Load STL file
  const geometry = useLoader(STLLoader, '/models/Grundfos CR 15 Pump.STL')
  
  // Center the geometry
  useEffect(() => {
    if (geometry) {
      geometry.center()
      geometry.computeVertexNormals()
    }
  }, [geometry])
  
  // Animate based on fault state
  useFrame((state) => {
    if (meshRef.current) {
      // Base rotation
      meshRef.current.rotation.y += 0.002
      
      // Add vibration effect based on fault
      if (faultState === 'BEARING_WEAR' || faultState === 'CAVITATION') {
        const vibrationIntensity = sensorData?.vibration ? sensorData.vibration / 50 : 0.01
        meshRef.current.position.x = Math.sin(state.clock.elapsedTime * 50) * vibrationIntensity
        meshRef.current.position.z = Math.cos(state.clock.elapsedTime * 50) * vibrationIntensity
      } else {
        meshRef.current.position.x = 0
        meshRef.current.position.z = 0
      }
    }
  })
  
  // Color based on fault state
  const getColor = () => {
    switch (faultState) {
      case 'WINDING_DEFECT':
        return '#ef4444' // Red
      case 'SUPPLY_FAULT':
        return '#f97316' // Orange
      case 'CAVITATION':
        return '#3b82f6' // Blue
      case 'BEARING_WEAR':
        return '#eab308' // Yellow
      case 'OVERLOAD':
        return '#dc2626' // Dark red
      default:
        return '#22c55e' // Green for normal
    }
  }
  
  // Emissive intensity based on temperature
  const getEmissive = () => {
    if (sensorData?.temperature > 70) {
      return '#ff4400'
    }
    return '#000000'
  }
  
  const emissiveIntensity = sensorData?.temperature 
    ? Math.max(0, (sensorData.temperature - 60) / 40) 
    : 0

  return (
    <mesh
      ref={meshRef}
      geometry={geometry}
      scale={0.015}
      rotation={[-Math.PI / 2, 0, 0]}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <meshStandardMaterial
        color={getColor()}
        metalness={0.8}
        roughness={0.2}
        emissive={getEmissive()}
        emissiveIntensity={emissiveIntensity}
      />
      {hovered && (
        <Html distanceFactor={100}>
          <div className="bg-gray-900/90 text-white px-3 py-2 rounded-lg text-sm whitespace-nowrap">
            <div className="font-bold">Grundfos CR 15 Pump</div>
            <div className="text-gray-300">State: {faultState || 'NORMAL'}</div>
          </div>
        </Html>
      )}
    </mesh>
  )
}

// Loading fallback
function LoadingFallback() {
  return (
    <Html center>
      <div className="flex flex-col items-center gap-2">
        <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-white text-sm">Loading 3D Model...</span>
      </div>
    </Html>
  )
}

// Status indicators floating around the pump
function StatusIndicators({ sensorData, faultState }) {
  if (!sensorData) return null
  
  const indicators = [
    { 
      label: 'Temperature', 
      value: `${sensorData.temperature?.toFixed(1)}°C`,
      position: [3, 2, 0],
      color: sensorData.temperature > 70 ? '#ef4444' : '#22c55e'
    },
    { 
      label: 'Vibration', 
      value: `${sensorData.vibration?.toFixed(2)} mm/s`,
      position: [-3, 2, 0],
      color: sensorData.vibration > 4 ? '#ef4444' : '#22c55e'
    },
    { 
      label: 'Pressure', 
      value: `${sensorData.pressure?.toFixed(1)} bar`,
      position: [0, 3.5, 0],
      color: sensorData.pressure < 3 ? '#ef4444' : '#22c55e'
    },
  ]
  
  return (
    <>
      {indicators.map((ind, i) => (
        <Html key={i} position={ind.position}>
          <div 
            className="px-2 py-1 rounded text-xs font-mono whitespace-nowrap"
            style={{ 
              backgroundColor: `${ind.color}20`,
              border: `1px solid ${ind.color}`,
              color: ind.color
            }}
          >
            <div className="text-gray-400 text-[10px]">{ind.label}</div>
            <div className="font-bold">{ind.value}</div>
          </div>
        </Html>
      ))}
    </>
  )
}

// Main 3D Viewer component
export default function PumpViewer3D({ faultState, sensorData, className = '' }) {
  return (
    <div className={`relative ${className}`}>
      {/* Status badge */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
        <div className={`px-3 py-1 rounded-full text-xs font-bold ${
          faultState === 'NORMAL' 
            ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
            : 'bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse'
        }`}>
          {faultState || 'NORMAL'}
        </div>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-10 text-xs text-gray-400">
        <div className="flex items-center gap-2">
          <span>🖱️ Drag to rotate</span>
          <span>•</span>
          <span>🔍 Scroll to zoom</span>
        </div>
      </div>
      
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [8, 6, 8], fov: 45 }}
        shadows
        gl={{ antialias: true }}
      >
        <color attach="background" args={['#0f172a']} />
        
        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <spotLight
          position={[10, 10, 10]}
          angle={0.3}
          penumbra={1}
          intensity={1}
          castShadow
        />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#60a5fa" />
        
        {/* Grid helper */}
        <gridHelper args={[20, 20, '#1e3a5f', '#0f172a']} />
        
        <Suspense fallback={<LoadingFallback />}>
          <PumpModel faultState={faultState} sensorData={sensorData} />
          <StatusIndicators sensorData={sensorData} faultState={faultState} />
          <ContactShadows
            position={[0, -2, 0]}
            opacity={0.5}
            scale={20}
            blur={2}
            far={4}
          />
          <Environment preset="city" />
        </Suspense>
        
        {/* Camera controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={5}
          maxDistance={20}
          autoRotate={false}
        />
      </Canvas>
    </div>
  )
}
