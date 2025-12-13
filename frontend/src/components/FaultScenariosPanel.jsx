import { useState, useEffect } from 'react'
import { 
  AlertTriangle, CheckCircle, Info, ChevronDown, ChevronUp,
  Wrench, Clock, Zap, Droplets, Settings, AlertOctagon,
  HelpCircle, RefreshCw, Shield, Activity
} from 'lucide-react'

// =====================================================
// Severity Badge Component
// =====================================================
function SeverityBadge({ severity, name }) {
  const styles = {
    0: { bg: 'bg-green-500/20', border: 'border-green-500/50', text: 'text-green-400', label: 'Normal' },
    1: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400', label: 'Niveau 1' },
    2: { bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400', label: 'Niveau 2' },
    3: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400', label: 'Niveau 3' },
    4: { bg: 'bg-red-600/30', border: 'border-red-600/70', text: 'text-red-300', label: 'CRITIQUE' },
  }
  
  const style = styles[severity] || styles[0]
  
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.border} ${style.text} border`}>
      {style.label}
    </span>
  )
}

// =====================================================
// Scenario Card Component (User-friendly)
// =====================================================
function ScenarioCard({ scenario, isActive, isAllowed, onSelect, onShowDetails }) {
  const severityColors = {
    0: 'from-green-500/10 to-emerald-500/10 border-green-500/30 hover:border-green-500/60',
    1: 'from-yellow-500/10 to-amber-500/10 border-yellow-500/30 hover:border-yellow-500/60',
    2: 'from-orange-500/10 to-amber-500/10 border-orange-500/30 hover:border-orange-500/60',
    3: 'from-red-500/10 to-rose-500/10 border-red-500/30 hover:border-red-500/60',
    4: 'from-red-600/20 to-rose-600/20 border-red-600/50 hover:border-red-600/80',
  }
  
  const activeStyles = {
    0: 'ring-4 ring-green-500 border-green-400 bg-green-500/20 shadow-lg shadow-green-500/30',
    1: 'ring-4 ring-yellow-500 border-yellow-400 bg-yellow-500/20 shadow-lg shadow-yellow-500/30',
    2: 'ring-4 ring-orange-500 border-orange-400 bg-orange-500/20 shadow-lg shadow-orange-500/30',
    3: 'ring-4 ring-red-500 border-red-400 bg-red-500/20 shadow-lg shadow-red-500/30',
    4: 'ring-4 ring-red-600 border-red-500 bg-red-600/30 shadow-lg shadow-red-600/40 animate-pulse',
  }
  
  const isNormal = scenario.id === 'NORMAL'
  
  return (
    <div 
      className={`
        relative rounded-xl p-4 border-2 transition-all duration-300 cursor-pointer
        bg-gradient-to-br ${severityColors[scenario.severity]}
        ${isActive ? activeStyles[scenario.severity] : ''}
        ${!isAllowed && !isNormal ? 'opacity-40 cursor-not-allowed grayscale' : ''}
        ${isActive ? 'scale-[1.02]' : 'hover:scale-[1.01]'}
      `}
      onClick={() => isAllowed && onSelect(scenario.id)}
    >
      {/* ACTIVE Badge - Very visible */}
      {isActive && (
        <div className="absolute -top-3 -right-3 z-10">
          <div className={`
            px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider
            flex items-center gap-1.5 shadow-lg
            ${scenario.severity === 0 
              ? 'bg-green-500 text-white' 
              : scenario.severity <= 2 
                ? 'bg-orange-500 text-white animate-pulse' 
                : 'bg-red-600 text-white animate-pulse'}
          `}>
            <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
            ACTIF
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-3xl ${isActive ? 'animate-bounce' : ''}`}>{scenario.icon}</span>
          <div>
            <h4 className={`font-semibold text-sm ${isActive ? 'text-white' : 'text-white'}`}>
              {scenario.display_name}
            </h4>
            <SeverityBadge severity={scenario.severity} name={scenario.severity_name} />
          </div>
        </div>
      </div>
      
      {/* Short Description */}
      <p className={`text-xs mt-2 line-clamp-2 ${isActive ? 'text-white/90' : 'text-slate-400'}`}>
        {scenario.description}
      </p>
      
      {/* Active indicator bar */}
      {isActive && (
        <div className={`
          absolute bottom-0 left-0 right-0 h-1 rounded-b-xl
          ${scenario.severity === 0 ? 'bg-green-500' : 
            scenario.severity <= 2 ? 'bg-orange-500' : 'bg-red-500'}
        `}>
          <div className="h-full bg-white/50 animate-pulse rounded-b-xl"></div>
        </div>
      )}
      
      {/* Blocked indicator */}
      {!isAllowed && !isNormal && (
        <div className="absolute inset-0 bg-slate-900/70 rounded-xl flex items-center justify-center backdrop-blur-sm">
          <div className="text-center p-2">
            <AlertOctagon className="w-8 h-8 text-slate-400 mx-auto mb-1" />
            <p className="text-slate-300 text-xs font-medium">Réparer d'abord</p>
          </div>
        </div>
      )}
      
      {/* Info button */}
      <button 
        onClick={(e) => { e.stopPropagation(); onShowDetails(scenario); }}
        className="absolute top-2 right-2 p-1.5 rounded-full hover:bg-white/20 transition-colors"
      >
        <HelpCircle className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400 hover:text-white'}`} />
      </button>
      
      {/* Normal state special styling */}
      {isNormal && !isActive && (
        <div className="mt-3 flex items-center gap-1 text-green-400 text-xs">
          <Wrench className="w-3 h-3" />
          <span>Cliquez pour réparer/réinitialiser</span>
        </div>
      )}
      
      {isNormal && isActive && (
        <div className="mt-3 flex items-center gap-1 text-green-300 text-xs font-medium">
          <CheckCircle className="w-4 h-4" />
          <span>Système en fonctionnement normal</span>
        </div>
      )}
    </div>
  )
}

// =====================================================
// Scenario Details Modal
// =====================================================
function ScenarioDetailsModal({ scenario, onClose, onActivate, isAllowed }) {
  if (!scenario) return null
  
  const categoryIcons = {
    electrical: <Zap className="w-5 h-5 text-yellow-400" />,
    hydraulic: <Droplets className="w-5 h-5 text-blue-400" />,
    mechanical: <Settings className="w-5 h-5 text-orange-400" />,
    normal: <CheckCircle className="w-5 h-5 text-green-400" />,
  }
  
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl">{scenario.icon}</span>
              <div>
                <h2 className="text-xl font-bold text-white">{scenario.display_name}</h2>
                <div className="flex items-center gap-2 mt-1">
                  {categoryIcons[scenario.category]}
                  <span className="text-slate-400 text-sm capitalize">{scenario.category}</span>
                  <SeverityBadge severity={scenario.severity} name={scenario.severity_name} />
                </div>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" />
              Description
            </h3>
            <p className="text-slate-300 text-sm leading-relaxed bg-slate-800/50 p-4 rounded-lg">
              {scenario.description}
            </p>
          </div>
          
          {/* Symptoms */}
          <div>
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Symptômes à observer
            </h3>
            <ul className="space-y-2">
              {scenario.symptoms.map((symptom, i) => (
                <li key={i} className="flex items-start gap-2 text-slate-300 text-sm">
                  <span className="text-amber-400 mt-1">•</span>
                  {symptom}
                </li>
              ))}
            </ul>
          </div>
          
          {/* Causes */}
          <div>
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-blue-400" />
              Causes possibles
            </h3>
            <ul className="space-y-2">
              {scenario.causes.map((cause, i) => (
                <li key={i} className="flex items-start gap-2 text-slate-300 text-sm">
                  <span className="text-blue-400 mt-1">•</span>
                  {cause}
                </li>
              ))}
            </ul>
          </div>
          
          {/* Repair Action */}
          <div className={`p-4 rounded-lg ${scenario.severity >= 3 ? 'bg-red-500/10 border border-red-500/30' : 'bg-green-500/10 border border-green-500/30'}`}>
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <Wrench className={`w-4 h-4 ${scenario.severity >= 3 ? 'text-red-400' : 'text-green-400'}`} />
              Action de réparation
            </h3>
            <p className={`text-sm ${scenario.severity >= 3 ? 'text-red-200' : 'text-green-200'}`}>
              {scenario.repair_action}
            </p>
            
            <div className="flex items-center gap-4 mt-3 text-slate-400 text-xs">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Temps estimé: {scenario.maintenance_time}
              </span>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-6 border-t border-slate-700 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Fermer
          </button>
          
          {scenario.id !== 'NORMAL' && (
            <button
              onClick={() => { onActivate(scenario.id); onClose(); }}
              disabled={!isAllowed}
              className={`
                px-6 py-2 rounded-lg font-semibold transition-all
                ${isAllowed 
                  ? 'bg-gradient-to-r from-amber-500 to-red-500 hover:from-amber-600 hover:to-red-600 text-white' 
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'}
              `}
            >
              {isAllowed ? '⚠️ Simuler ce défaut' : '🔒 Réparer d\'abord'}
            </button>
          )}
          
          {scenario.id === 'NORMAL' && (
            <button
              onClick={() => { onActivate('NORMAL'); onClose(); }}
              className="px-6 py-2 rounded-lg font-semibold bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white transition-all"
            >
              ✅ Réparer / Réinitialiser
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// =====================================================
// Main Fault Scenarios Panel (User-friendly)
// =====================================================
export default function FaultScenariosPanel({ onInjectFault, activeFault, connected }) {
  const [scenarios, setScenarios] = useState(null)
  const [currentState, setCurrentState] = useState(null)
  const [allowedTransitions, setAllowedTransitions] = useState([])
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [isExpanded, setIsExpanded] = useState(true)
  const [lastMessage, setLastMessage] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  
  // Fetch scenarios on mount
  useEffect(() => {
    fetchScenarios()
  }, [])
  
  // Re-fetch when active fault changes
  useEffect(() => {
    fetchScenarios()
  }, [activeFault])
  
  const fetchScenarios = async () => {
    try {
      const response = await fetch('/api/fault-types')
      if (response.ok) {
        const data = await response.json()
        setScenarios(data.scenarios)
        setCurrentState(data.current_state)
        setAllowedTransitions(data.allowed_transitions || [])
      }
    } catch (error) {
      console.error('Failed to fetch scenarios:', error)
    }
  }
  
  const handleSelectScenario = async (scenarioId) => {
    if (!connected) {
      setLastMessage({ type: 'error', text: '❌ Non connecté au backend' })
      return
    }
    
    setIsLoading(true)
    setLastMessage(null)
    
    try {
      const response = await fetch('/api/inject-fault', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fault_type: scenarioId })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setLastMessage({ 
          type: data.is_repair ? 'success' : 'warning', 
          text: data.message 
        })
        onInjectFault(scenarioId)
        fetchScenarios() // Refresh state
      } else {
        setLastMessage({ 
          type: 'error', 
          text: data.message,
          hint: data.hint
        })
      }
    } catch (error) {
      setLastMessage({ type: 'error', text: `Erreur: ${error.message}` })
    } finally {
      setIsLoading(false)
    }
  }
  
  const showDetails = (scenario) => {
    setSelectedScenario(scenario)
  }
  
  if (!scenarios) {
    return (
      <div className="glass rounded-xl p-6">
        <div className="flex items-center justify-center gap-3 text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Chargement des scénarios...</span>
        </div>
      </div>
    )
  }
  
  return (
    <div className="glass rounded-xl overflow-hidden">
      {/* Current State Banner - Very visible */}
      {currentState && (
        <div className={`
          p-4 border-b-2 transition-all duration-300
          ${currentState.id === 'NORMAL' 
            ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-500/50' 
            : currentState.severity <= 2
              ? 'bg-gradient-to-r from-orange-500/20 to-amber-500/20 border-orange-500/50'
              : 'bg-gradient-to-r from-red-500/30 to-rose-500/30 border-red-500/50 animate-pulse'}
        `}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`
                w-12 h-12 rounded-full flex items-center justify-center text-2xl
                ${currentState.id === 'NORMAL' 
                  ? 'bg-green-500/30 ring-2 ring-green-400' 
                  : currentState.severity <= 2
                    ? 'bg-orange-500/30 ring-2 ring-orange-400 animate-pulse'
                    : 'bg-red-500/30 ring-2 ring-red-400 animate-bounce'}
              `}>
                {scenarios?.[currentState.severity === 0 ? 'normal' : 
                  currentState.severity === 1 ? 'low' : 
                  currentState.severity === 2 ? 'medium' : 
                  currentState.severity === 3 ? 'high' : 'critical']?.scenarios?.find(s => s.id === currentState.id)?.icon || '⚙️'}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className={`font-bold text-lg ${
                    currentState.id === 'NORMAL' ? 'text-green-400' : 
                    currentState.severity <= 2 ? 'text-orange-400' : 'text-red-400'
                  }`}>
                    ÉTAT ACTUEL: {currentState.display_name}
                  </h3>
                  <span className={`
                    px-2 py-0.5 rounded-full text-xs font-bold uppercase
                    ${currentState.id === 'NORMAL' 
                      ? 'bg-green-500 text-white' 
                      : currentState.severity <= 2
                        ? 'bg-orange-500 text-white'
                        : 'bg-red-500 text-white animate-pulse'}
                  `}>
                    {currentState.id === 'NORMAL' ? '✓ OK' : '⚠ DÉFAUT'}
                  </span>
                </div>
                <p className="text-slate-300 text-sm mt-1">
                  {currentState.id === 'NORMAL' 
                    ? 'La pompe fonctionne normalement. Tous les paramètres sont dans les limites.'
                    : `Défaut de niveau ${currentState.severity} détecté. Consultez le diagnostic AI.`}
                </p>
              </div>
            </div>
            
            {currentState.id !== 'NORMAL' && (
              <button
                onClick={(e) => { e.stopPropagation(); handleSelectScenario('NORMAL'); }}
                className="px-6 py-3 rounded-xl bg-green-500 hover:bg-green-600 text-white 
                         font-bold transition-all shadow-lg shadow-green-500/30 flex items-center gap-2
                         hover:scale-105"
              >
                <Wrench className="w-5 h-5" />
                RÉPARER
              </button>
            )}
          </div>
        </div>
      )}
      
      {/* Header with toggle */}
      <div 
        className="p-4 bg-gradient-to-r from-slate-800/50 to-slate-700/50 border-b border-slate-700/50 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="font-semibold text-white">🧪 Panneau de Simulation de Pannes</h3>
              <p className="text-xs text-slate-400">
                Cliquez sur un scénario pour simuler un défaut • 
                <span className="text-cyan-400"> État actuel: {currentState?.display_name || 'Normal'}</span>
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {currentState && currentState.id !== 'NORMAL' && (
              <button
                onClick={(e) => { e.stopPropagation(); handleSelectScenario('NORMAL'); }}
                className="px-4 py-2 rounded-lg bg-green-500/20 border border-green-500/50 text-green-400 
                         hover:bg-green-500/30 transition-colors text-sm font-medium flex items-center gap-2"
              >
                <Wrench className="w-4 h-4" />
                Réparer
              </button>
            )}
            
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </div>
        </div>
        
        {/* Message Toast */}
        {lastMessage && (
          <div className={`
            mt-3 p-3 rounded-lg text-sm
            ${lastMessage.type === 'success' ? 'bg-green-500/20 text-green-300 border border-green-500/30' : ''}
            ${lastMessage.type === 'warning' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : ''}
            ${lastMessage.type === 'error' ? 'bg-red-500/20 text-red-300 border border-red-500/30' : ''}
          `}>
            <p>{lastMessage.text}</p>
            {lastMessage.hint && (
              <p className="text-xs mt-1 opacity-80">{lastMessage.hint}</p>
            )}
          </div>
        )}
      </div>
      
      {/* Scenarios Grid */}
      {isExpanded && (
        <div className="p-4 space-y-6">
          {/* Instructions */}
          <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
            <h4 className="text-white font-medium mb-2 flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" />
              Guide d'utilisation
            </h4>
            <ul className="text-slate-400 text-sm space-y-1">
              <li>• <span className="text-green-400">Vert</span>: État normal - Cliquez pour réparer</li>
              <li>• <span className="text-yellow-400">Jaune</span>: Avertissements légers (Niveau 1)</li>
              <li>• <span className="text-orange-400">Orange</span>: Problèmes modérés (Niveau 2)</li>
              <li>• <span className="text-red-400">Rouge</span>: Problèmes sérieux (Niveau 3)</li>
              <li>• <span className="text-red-300">Rouge foncé</span>: CRITIQUE - Arrêt immédiat (Niveau 4)</li>
              <li className="text-cyan-400 mt-2">💡 Règle: Vous ne pouvez pas passer d'un état grave à un état moins grave sans réparer d'abord.</li>
            </ul>
          </div>
          
          {/* Normal State (Always visible at top) */}
          <div>
            <h4 className="text-slate-400 text-xs uppercase tracking-wider mb-3">
              ✅ Fonctionnement Normal
            </h4>
            <div className="grid grid-cols-1">
              {scenarios.normal?.scenarios.map(scenario => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  isActive={activeFault === scenario.id}
                  isAllowed={allowedTransitions.includes(scenario.id)}
                  onSelect={handleSelectScenario}
                  onShowDetails={showDetails}
                />
              ))}
            </div>
          </div>
          
          {/* Level 1 - Warnings */}
          {scenarios.low?.scenarios.length > 0 && (
            <div>
              <h4 className="text-yellow-400 text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
                🔶 {scenarios.low.name}
                <span className="text-slate-500 normal-case">- {scenarios.low.description}</span>
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {scenarios.low.scenarios.map(scenario => (
                  <ScenarioCard
                    key={scenario.id}
                    scenario={scenario}
                    isActive={activeFault === scenario.id}
                    isAllowed={allowedTransitions.includes(scenario.id)}
                    onSelect={handleSelectScenario}
                    onShowDetails={showDetails}
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Level 2 - Medium */}
          {scenarios.medium?.scenarios.length > 0 && (
            <div>
              <h4 className="text-orange-400 text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
                🟠 {scenarios.medium.name}
                <span className="text-slate-500 normal-case">- {scenarios.medium.description}</span>
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {scenarios.medium.scenarios.map(scenario => (
                  <ScenarioCard
                    key={scenario.id}
                    scenario={scenario}
                    isActive={activeFault === scenario.id}
                    isAllowed={allowedTransitions.includes(scenario.id)}
                    onSelect={handleSelectScenario}
                    onShowDetails={showDetails}
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Level 3 - High */}
          {scenarios.high?.scenarios.length > 0 && (
            <div>
              <h4 className="text-red-400 text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
                🔴 {scenarios.high.name}
                <span className="text-slate-500 normal-case">- {scenarios.high.description}</span>
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {scenarios.high.scenarios.map(scenario => (
                  <ScenarioCard
                    key={scenario.id}
                    scenario={scenario}
                    isActive={activeFault === scenario.id}
                    isAllowed={allowedTransitions.includes(scenario.id)}
                    onSelect={handleSelectScenario}
                    onShowDetails={showDetails}
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Level 4 - Critical */}
          {scenarios.critical?.scenarios.length > 0 && (
            <div>
              <h4 className="text-red-300 text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
                ⛔ {scenarios.critical.name}
                <span className="text-slate-500 normal-case">- {scenarios.critical.description}</span>
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {scenarios.critical.scenarios.map(scenario => (
                  <ScenarioCard
                    key={scenario.id}
                    scenario={scenario}
                    isActive={activeFault === scenario.id}
                    isAllowed={allowedTransitions.includes(scenario.id)}
                    onSelect={handleSelectScenario}
                    onShowDetails={showDetails}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Details Modal */}
      {selectedScenario && (
        <ScenarioDetailsModal
          scenario={selectedScenario}
          onClose={() => setSelectedScenario(null)}
          onActivate={handleSelectScenario}
          isAllowed={allowedTransitions.includes(selectedScenario.id)}
        />
      )}
      
      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-slate-900/50 flex items-center justify-center">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        </div>
      )}
    </div>
  )
}
