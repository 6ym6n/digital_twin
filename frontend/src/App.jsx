import { useState, useEffect, useRef, useCallback } from 'react'
import { 
  Zap, Gauge, Activity, Thermometer, 
  Droplets, MessageSquare, AlertTriangle, 
  CheckCircle, RefreshCw, Send, Bot, User, Box,
  X, Minimize2, Maximize2, Sparkles
} from 'lucide-react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine,
  ReferenceArea, AreaChart, Area, ComposedChart
} from 'recharts'
import PumpViewer3D from './components/PumpViewer3D'

// API Base URL
const API_BASE = ''  // Empty for Vite proxy

// =====================================================
// Sparkline Component (Mini Chart)
// =====================================================
function Sparkline({ data, dataKey, color, height = 40 }) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <defs>
            <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <Area 
            type="monotone" 
            dataKey={dataKey} 
            stroke={color} 
            strokeWidth={1.5}
            fill={`url(#gradient-${dataKey})`}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

// =====================================================
// Metric Card Component with Sparkline
// =====================================================
function MetricCard({ title, value, unit, icon: Icon, status = 'normal', subValues = null, sparklineData = [], sparklineKey = 'value', threshold = null }) {
  const statusColors = {
    normal: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
    warning: 'from-amber-500/20 to-orange-500/20 border-amber-500/30',
    danger: 'from-red-500/20 to-rose-500/20 border-red-500/30 pulse-danger',
    success: 'from-green-500/20 to-emerald-500/20 border-green-500/30',
  }

  const iconColors = {
    normal: 'text-blue-400',
    warning: 'text-amber-400',
    danger: 'text-red-400',
    success: 'text-green-400',
  }

  const sparklineColors = {
    normal: '#3b82f6',
    warning: '#f59e0b',
    danger: '#ef4444',
    success: '#22c55e',
  }

  return (
    <div className={`glass rounded-xl p-4 bg-gradient-to-br ${statusColors[status]} transition-all duration-300 ${status === 'danger' ? 'animate-pulse' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-slate-400 text-sm font-medium">{title}</span>
        <Icon className={`w-5 h-5 ${iconColors[status]}`} />
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold text-white mono">
          {typeof value === 'number' ? value.toFixed(2) : value}
        </span>
        <span className="text-slate-400 text-sm">{unit}</span>
      </div>
      {subValues && (
        <div className="mt-2 flex gap-3 text-xs text-slate-400">
          {subValues.map((sv, i) => (
            <span key={i} className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${sv.color}`}></span>
              {sv.label}: <span className="mono text-slate-300">{sv.value}</span>
            </span>
          ))}
        </div>
      )}
      
      {/* Sparkline */}
      {sparklineData.length > 0 && (
        <div className="mt-3 -mx-1">
          <Sparkline 
            data={sparklineData} 
            dataKey={sparklineKey} 
            color={sparklineColors[status]} 
          />
        </div>
      )}
      
      {/* Threshold indicator */}
      {threshold && (
        <div className={`mt-2 text-xs ${status === 'normal' ? 'text-green-400' : 'text-red-400'}`}>
          {status === 'normal' ? '✓' : '⚠'} {threshold}
        </div>
      )}
    </div>
  )
}

// =====================================================
// Fault Button Component
// =====================================================
function FaultButton({ id, name, icon, active, onClick, disabled }) {
  const isNormal = id === 'NORMAL'
  
  return (
    <button
      onClick={() => onClick(id)}
      disabled={disabled}
      className={`
        flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
        transition-all duration-200 
        ${active 
          ? (isNormal 
              ? 'bg-green-500/20 border border-green-500/50 text-green-400 shadow-glow-success' 
              : 'bg-red-500/20 border border-red-500/50 text-red-400 shadow-glow-danger')
          : 'glass-light hover:bg-slate-700/50 text-slate-300 hover:text-white'
        }
        disabled:opacity-50 disabled:cursor-not-allowed
      `}
    >
      <span>{icon}</span>
      <span>{name}</span>
    </button>
  )
}

// =====================================================
// Diagnosis Panel Component with Shutdown Decision
// =====================================================
function DiagnosisPanel({ diagnosis, shutdownDecision, isLoading, onRefresh, onEmergencyStop, activeFault }) {
  // Determine shutdown banner style
  const getShutdownStyle = () => {
    if (!shutdownDecision) return null
    
    switch (shutdownDecision.action) {
      case 'IMMEDIATE_SHUTDOWN':
        return {
          bg: 'bg-red-500/20 border-red-500',
          text: 'text-red-400',
          icon: '⛔',
          animate: 'animate-pulse'
        }
      case 'CONTINUE_THEN_STOP':
        return {
          bg: 'bg-amber-500/20 border-amber-500',
          text: 'text-amber-400',
          icon: '⚠️',
          animate: ''
        }
      default:
        return {
          bg: 'bg-green-500/20 border-green-500',
          text: 'text-green-400',
          icon: '✅',
          animate: ''
        }
    }
  }
  
  const style = getShutdownStyle()

  const renderInlineBold = (text) => {
    if (!text || typeof text !== 'string' || !text.includes('**')) return text

    const parts = []
    const regex = /\*\*(.+?)\*\*/g
    let lastIndex = 0
    let match
    let keyIndex = 0

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(<span key={`t-${keyIndex++}`}>{text.slice(lastIndex, match.index)}</span>)
      }
      parts.push(
        <span key={`b-${keyIndex++}`} className="font-semibold text-slate-100">
          {match[1]}
        </span>
      )
      lastIndex = match.index + match[0].length
    }

    if (lastIndex < text.length) {
      parts.push(<span key={`t-${keyIndex++}`}>{text.slice(lastIndex)}</span>)
    }

    return parts
  }

  const parseDiagnosisText = (text) => {
    const input = (text || '').replace(/\r\n/g, '\n').trim()
    if (!input) return null

    const lines = input.split('\n')
    const sections = {
      diagnosis: [],
      rootCause: [],
      actionItems: [],
      verificationSteps: [],
      recommendation: []
    }

    const normalizeHeaderKey = (raw) => {
      const upper = String(raw || '').toUpperCase().replace(/\s+/g, ' ').trim()
      if (upper === 'DIAGNOSIS') return 'diagnosis'
      if (upper === 'ROOT CAUSE') return 'rootCause'
      if (upper === 'ACTION ITEM' || upper === 'ACTION ITEMS') return 'actionItems'
      if (upper === 'VERIFICATION STEP' || upper === 'VERIFICATION STEPS') return 'verificationSteps'
      if (upper === 'RECOMMENDATION') return 'recommendation'
      return null
    }

    const headerRegex = /^(?:#+\s*)?(?:\*\*)?\s*(DIAGNOSIS|ROOT\s*CAUSE|ACTION\s*ITEMS?|VERIFICATION\s*STEPS?|RECOMMENDATION)\s*(?:\*\*)?\s*:?\s*$/i

    let currentKey = 'diagnosis'
    for (const rawLine of lines) {
      const line = rawLine ?? ''
      const trimmed = String(line).trim()
      const headerMatch = trimmed.match(headerRegex)

      if (headerMatch) {
        const key = normalizeHeaderKey(headerMatch[1])
        if (key) currentKey = key
        continue
      }

      sections[currentKey].push(line)
    }

    const toText = (arr) => arr.join('\n').trim()
    const extractBullets = (raw) => {
      const items = []
      for (const ln of raw.split('\n')) {
        const m = ln.match(/^\s*(?:[-*•]|\d+[.)])\s+(.+?)\s*$/)
        if (m) items.push(m[1])
      }
      return items
    }

    const diagnosisText = toText(sections.diagnosis)
    const rootCauseText = toText(sections.rootCause)
    const recommendationText = toText(sections.recommendation)

    const actionRaw = toText(sections.actionItems)
    const verificationRaw = toText(sections.verificationSteps)
    const actionItems = actionRaw ? extractBullets(actionRaw) : []
    const verificationSteps = verificationRaw ? extractBullets(verificationRaw) : []

    const hasStructured = Boolean(rootCauseText || recommendationText || actionItems.length || verificationSteps.length)

    return {
      diagnosisText,
      rootCauseText,
      recommendationText,
      actionItems,
      verificationSteps,
      fallbackText: input,
      hasStructured
    }
  }

  const parsedDiagnosis = diagnosis ? parseDiagnosisText(diagnosis) : null

  const renderParagraphs = (text) => {
    const value = (text || '').trim()
    if (!value) return null
    const paragraphs = value.split(/\n\s*\n/g)
    return (
      <div className="space-y-2">
        {paragraphs.map((p, idx) => (
          <p key={idx} className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
            {renderInlineBold(p)}
          </p>
        ))}
      </div>
    )
  }

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-cyan-400" />
          <h3 className="font-semibold text-white">AI Diagnosis</h3>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-2 rounded-lg glass-light hover:bg-slate-700/50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 text-slate-300 ${isLoading ? 'animate-spin' : ''}`} />
          <span className="text-slate-200 text-sm font-medium">Diagnose</span>
        </button>
      </div>

      {/* Fault prompt (manual diagnosis) */}
      {activeFault && activeFault !== 'NORMAL' && !diagnosis && !isLoading && (
        <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span className="text-amber-200 text-sm">
                Défaut détecté: <span className="font-semibold">{activeFault.replace('_', ' ')}</span>. Cliquez sur <span className="font-semibold">Diagnose</span>.
              </span>
            </div>
          </div>
        </div>
      )}
      
      {/* Shutdown Decision Banner */}
      {shutdownDecision && shutdownDecision.action !== 'NORMAL_OPERATION' && (
        <div className={`mb-4 p-4 rounded-lg border-2 ${style.bg} ${style.animate}`}>
          <div className="flex items-start gap-3">
            <span className="text-2xl">{style.icon}</span>
            <div className="flex-1">
              <h4 className={`font-bold ${style.text} mb-1`}>
                {shutdownDecision.action === 'IMMEDIATE_SHUTDOWN' 
                  ? '🚨 ARRÊT IMMÉDIAT REQUIS' 
                  : '⚠️ ATTENTION REQUISE'}
              </h4>
              <p className={`text-sm ${style.text} mb-2`}>
                {shutdownDecision.message}
              </p>
              
              {/* Critical Conditions */}
              {shutdownDecision.critical_conditions?.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs text-red-300 font-semibold mb-1">Conditions critiques:</p>
                  {shutdownDecision.critical_conditions.map((cond, i) => (
                    <div key={i} className="text-xs text-red-200 ml-2">
                      • {cond.parameter}: <span className="font-mono font-bold">{cond.value}</span> 
                      <span className="text-red-400"> (seuil: {cond.threshold})</span>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Warning Conditions */}
              {shutdownDecision.warning_conditions?.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs text-amber-300 font-semibold mb-1">Avertissements:</p>
                  {shutdownDecision.warning_conditions.map((cond, i) => (
                    <div key={i} className="text-xs text-amber-200 ml-2">
                      • {cond.parameter}: <span className="font-mono font-bold">{cond.value}</span>
                      <span className="text-amber-400"> (seuil: {cond.threshold})</span>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Recommendation */}
              <div className={`mt-2 pt-2 border-t ${shutdownDecision.action === 'IMMEDIATE_SHUTDOWN' ? 'border-red-500/30' : 'border-amber-500/30'}`}>
                <p className="text-xs text-slate-300">
                  <span className="font-semibold">📋 Recommandation:</span> {shutdownDecision.recommendation}
                </p>
              </div>
              
              {/* Emergency Stop Button */}
              {onEmergencyStop && (
                <button
                  onClick={() => onEmergencyStop('Manual emergency stop')}
                  className={`mt-3 w-full py-2 px-4 rounded-lg font-bold text-sm transition-all
                    ${shutdownDecision.action === 'IMMEDIATE_SHUTDOWN' 
                      ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse' 
                      : 'bg-amber-600 hover:bg-amber-700 text-white'}
                  `}
                >
                  🛑 {shutdownDecision.action === 'IMMEDIATE_SHUTDOWN' 
                    ? 'ARRÊT D\'URGENCE IMMÉDIAT' 
                    : 'ARRÊTER APRÈS DIAGNOSTIC'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Normal Operation Banner */}
      {shutdownDecision && shutdownDecision.action === 'NORMAL_OPERATION' && diagnosis && (
        <div className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/30">
          <div className="flex items-center gap-2">
            <span className="text-lg">✅</span>
            <span className="text-green-400 text-sm font-medium">
              Fonctionnement normal - Aucune action requise
            </span>
          </div>
        </div>
      )}
      
      <div className="bg-slate-800/50 rounded-lg p-4 max-h-64 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center gap-3 text-slate-400">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span>Analyzing sensor data...</span>
          </div>
        ) : diagnosis ? (
          <div className="slide-in space-y-3">
            {parsedDiagnosis?.hasStructured ? (
              <>
                {parsedDiagnosis.diagnosisText && (
                  <div className="rounded-lg border border-slate-700/50 bg-slate-900/30 p-3">
                    <div className="text-xs font-semibold text-cyan-300 mb-2">Diagnosis</div>
                    {renderParagraphs(parsedDiagnosis.diagnosisText)}
                  </div>
                )}

                {parsedDiagnosis.rootCauseText && (
                  <div className="rounded-lg border border-slate-700/50 bg-slate-900/30 p-3">
                    <div className="text-xs font-semibold text-purple-300 mb-2">Root cause</div>
                    {renderParagraphs(parsedDiagnosis.rootCauseText)}
                  </div>
                )}

                {parsedDiagnosis.actionItems?.length > 0 && (
                  <div className="rounded-lg border border-slate-700/50 bg-slate-900/30 p-3">
                    <div className="text-xs font-semibold text-amber-300 mb-2">Action items</div>
                    <ol className="list-decimal ml-5 space-y-1 text-slate-300 text-sm">
                      {parsedDiagnosis.actionItems.map((item, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {renderInlineBold(item)}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {parsedDiagnosis.verificationSteps?.length > 0 && (
                  <div className="rounded-lg border border-slate-700/50 bg-slate-900/30 p-3">
                    <div className="text-xs font-semibold text-slate-200 mb-2">Verification</div>
                    <ul className="list-disc ml-5 space-y-1 text-slate-300 text-sm">
                      {parsedDiagnosis.verificationSteps.map((item, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {renderInlineBold(item)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {parsedDiagnosis.recommendationText && (
                  <div className="rounded-lg border border-slate-700/50 bg-slate-900/30 p-3">
                    <div className="text-xs font-semibold text-green-300 mb-2">Recommendation</div>
                    {renderParagraphs(parsedDiagnosis.recommendationText)}
                  </div>
                )}
              </>
            ) : (
              <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                {renderInlineBold(parsedDiagnosis?.fallbackText || diagnosis)}
              </div>
            )}
          </div>
        ) : (
          <div className="text-slate-500 text-sm italic">
            {activeFault && activeFault !== 'NORMAL'
              ? 'Défaut détecté. Cliquez sur Diagnose pour lancer le diagnostic.'
              : 'Inject a fault to see AI diagnosis, then click Diagnose to analyze current state.'}
          </div>
        )}
      </div>
    </div>
  )
}

// =====================================================
// Floating Chatbox Component
// =====================================================
function FloatingChatbox({ messages, onSendMessage, isLoading }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [input, setInput] = useState('')
  const [unreadCount, setUnreadCount] = useState(0)
  const messagesEndRef = useRef(null)

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen, isMinimized])

  // Track unread messages when closed
  useEffect(() => {
    if (!isOpen && messages.length > 0) {
      const lastMsg = messages[messages.length - 1]
      if (lastMsg.role === 'assistant') {
        setUnreadCount(prev => prev + 1)
      }
    }
  }, [messages, isOpen])

  // Clear unread when opened
  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0)
    }
  }, [isOpen])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  const quickQuestions = [
    "What's the current pump status?",
    "How to fix cavitation?",
    "Explain bearing wear symptoms",
    "Maintenance schedule?"
  ]

  const renderInlineBold = (text) => {
    if (!text || typeof text !== 'string' || !text.includes('**')) return text

    const parts = []
    const regex = /\*\*(.+?)\*\*/g
    let lastIndex = 0
    let match
    let keyIndex = 0

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(<span key={`t-${keyIndex++}`}>{text.slice(lastIndex, match.index)}</span>)
      }
      parts.push(
        <span key={`b-${keyIndex++}`} className="font-semibold text-slate-100">
          {match[1]}
        </span>
      )
      lastIndex = match.index + match[0].length
    }

    if (lastIndex < text.length) {
      parts.push(<span key={`t-${keyIndex++}`}>{text.slice(lastIndex)}</span>)
    }

    return parts
  }

  const renderChatContent = (content) => {
    const text = String(content || '').replace(/\r\n/g, '\n').trim()
    if (!text) return null

    const blocks = text.split(/\n\s*\n/g)

    return (
      <div className="space-y-2">
        {blocks.map((block, blockIdx) => {
          const lines = block.split('\n').filter(l => l.trim().length > 0)

          const isOrdered = lines.length > 0 && lines.every(l => /^\s*\d+\.\s+/.test(l))
          if (isOrdered) {
            return (
              <ol key={blockIdx} className="list-decimal ml-5 space-y-1">
                {lines.map((l, idx) => (
                  <li key={idx} className="text-sm leading-relaxed break-words">
                    {renderInlineBold(l.replace(/^\s*\d+\.\s+/, ''))}
                  </li>
                ))}
              </ol>
            )
          }

          const isUnordered = lines.length > 0 && lines.every(l => /^\s*[-*•]\s+/.test(l))
          if (isUnordered) {
            return (
              <ul key={blockIdx} className="list-disc ml-5 space-y-1">
                {lines.map((l, idx) => (
                  <li key={idx} className="text-sm leading-relaxed break-words">
                    {renderInlineBold(l.replace(/^\s*[-*•]\s+/, ''))}
                  </li>
                ))}
              </ul>
            )
          }

          return (
            <p key={blockIdx} className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {renderInlineBold(block)}
            </p>
          )
        })}
      </div>
    )
  }

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-cyan-500 to-blue-600 
                     rounded-full shadow-lg shadow-cyan-500/30 flex items-center justify-center
                     hover:scale-110 transition-all duration-300 z-50 group"
        >
          <Bot className="w-8 h-8 text-white" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full 
                           flex items-center justify-center text-white text-xs font-bold
                           animate-pulse">
              {unreadCount}
            </span>
          )}
          <span className="absolute right-full mr-3 px-3 py-1 bg-slate-800 text-white text-sm 
                         rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            AI Maintenance Assistant
          </span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div 
          className={`fixed bottom-6 right-6 z-50 transition-all duration-300 ease-out
                      ${isMinimized ? 'w-72 h-14' : 'w-96 h-[600px]'}`}
        >
          <div className="w-full h-full bg-slate-900/95 backdrop-blur-xl rounded-2xl 
                        border border-slate-700/50 shadow-2xl shadow-black/50 flex flex-col overflow-hidden">
            
            {/* Header */}
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 
                          border-b border-slate-700/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 
                              flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white text-sm">Maintenance AI</h3>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    <span className="text-xs text-green-400">Online • Gemini 2.5</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                >
                  {isMinimized ? (
                    <Maximize2 className="w-4 h-4 text-slate-400" />
                  ) : (
                    <Minimize2 className="w-4 h-4 text-slate-400" />
                  )}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-slate-400 hover:text-red-400" />
                </button>
              </div>
            </div>

            {/* Chat Content (hidden when minimized) */}
            {!isMinimized && (
              <>
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length === 0 ? (
                    <div className="text-center py-6">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 
                                    flex items-center justify-center">
                        <Sparkles className="w-8 h-8 text-cyan-400" />
                      </div>
                      <h4 className="text-white font-medium mb-2">AI Maintenance Assistant</h4>
                      <p className="text-slate-400 text-sm mb-4">
                        Ask me anything about the Grundfos CR pump, troubleshooting, or current sensor readings.
                      </p>
                      
                      {/* Quick Questions */}
                      <div className="space-y-2">
                        <p className="text-xs text-slate-500">Quick questions:</p>
                        <div className="flex flex-wrap gap-2 justify-center">
                          {quickQuestions.map((q, i) => (
                            <button
                              key={i}
                              onClick={() => onSendMessage(q)}
                              className="px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 
                                       rounded-full text-xs text-slate-300 hover:bg-cyan-500/20 
                                       hover:border-cyan-500/50 hover:text-cyan-300 transition-all"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    messages.map((msg, i) => (
                      <div
                        key={i}
                        className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        {msg.role === 'assistant' && (
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 
                                        flex items-center justify-center flex-shrink-0">
                            <Bot className="w-4 h-4 text-white" />
                          </div>
                        )}
                        <div
                          className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                              : 'bg-slate-800/80 text-slate-200 border border-slate-700/50'
                          }`}
                        >
                          {msg.role === 'assistant' ? (
                            <div className="text-slate-200">
                              {renderChatContent(msg.content)}
                            </div>
                          ) : (
                            <p className="text-sm whitespace-pre-wrap leading-relaxed break-words">
                              {msg.content}
                            </p>
                          )}
                        </div>
                        {msg.role === 'user' && (
                          <div className="w-8 h-8 rounded-full bg-slate-700 
                                        flex items-center justify-center flex-shrink-0">
                            <User className="w-4 h-4 text-slate-300" />
                          </div>
                        )}
                      </div>
                    ))
                  )}
                  
                  {/* Typing Indicator */}
                  {isLoading && (
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 
                                    flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="bg-slate-800/80 rounded-2xl px-4 py-3 border border-slate-700/50">
                        <div className="flex gap-1.5">
                          <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></span>
                          <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                          <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <form onSubmit={handleSubmit} className="p-4 border-t border-slate-700/50 bg-slate-900/50">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Type your message..."
                      className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 
                               text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50
                               focus:ring-2 focus:ring-cyan-500/20 transition-all text-sm"
                    />
                    <button
                      type="submit"
                      disabled={!input.trim() || isLoading}
                      className="px-4 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl
                               text-white hover:shadow-lg hover:shadow-cyan-500/30 transition-all
                               disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}

// =====================================================
// Live Chart Component with Reference Lines
// =====================================================
function LiveChart({ data, activeFault }) {
  const chartData = data.map((reading, index) => ({
    time: index,
    phase_a: reading.amperage?.phase_a || 0,
    phase_b: reading.amperage?.phase_b || 0,
    phase_c: reading.amperage?.phase_c || 0,
  }))

  // Calculate statistics
  const latestData = data[data.length - 1]
  const avgCurrent = latestData?.amperage?.average || 0
  const peakCurrent = Math.max(
    ...data.slice(-30).map(d => Math.max(d.amperage?.phase_a || 0, d.amperage?.phase_b || 0, d.amperage?.phase_c || 0))
  )
  const imbalance = latestData?.amperage?.imbalance_pct || 0

  const hasImbalance = imbalance > 5
  const hasFault = activeFault !== 'NORMAL'
  const hasWarning = hasImbalance || hasFault

  return (
    <div className={`glass rounded-xl p-4 transition-all duration-300 ${hasWarning ? 'ring-2 ring-amber-500/50' : ''}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="font-semibold text-white">⚡ Three-Phase Current Monitoring (Last 60s)</h3>
            <div className="text-xs text-slate-400 mt-1">
              Plage OK: imbalance &lt; 5% • Référence: 10A • Surcharge: &gt; 11.5A
            </div>
          </div>
        </div>
        {hasWarning && (
          <span className="px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-medium">
            {hasImbalance ? '⚠️ Imbalance Detected' : '⚠️ Fault Active'}
          </span>
        )}
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="overloadGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3}/>
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.05}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.2)" />
            
            {/* Overload Zone */}
            <ReferenceArea 
              y1={11.5} 
              y2={20} 
              fill="url(#overloadGradient)" 
              label={{ value: 'Overload Zone', position: 'insideTopRight', fill: '#ef4444', fontSize: 10 }}
            />
            
            {/* Rated Current Reference */}
            <ReferenceLine 
              y={10} 
              stroke="#64748b" 
              strokeDasharray="5 5" 
              label={{ value: 'Rated (10A)', position: 'insideBottomRight', fill: '#64748b', fontSize: 10 }}
            />
            
            <XAxis 
              dataKey="time" 
              stroke="#64748b" 
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickFormatter={(v) => `-${60 - v}s`}
            />
            <YAxis 
              stroke="#64748b" 
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              domain={[0, 20]}
              tickFormatter={(v) => `${v}A`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(30, 41, 59, 0.95)',
                border: '1px solid rgba(100, 116, 139, 0.3)',
                borderRadius: '8px',
                color: '#e2e8f0',
              }}
              labelFormatter={(v) => `${60 - v} seconds ago`}
              formatter={(value, name) => [`${value.toFixed(2)} A`, name]}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value) => <span className="text-slate-300 text-sm">{value}</span>}
            />
            <Line
              type="monotone"
              dataKey="phase_a"
              name="Phase A"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="phase_b"
              name="Phase B"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="phase_c"
              name="Phase C"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Stats Bar */}
      <div className="mt-4 flex items-center gap-6 text-sm">
        <span className="text-slate-400">
          📈 Current Status:
        </span>
        <span className="text-slate-300">
          Average: <span className="mono text-white font-medium">{avgCurrent.toFixed(1)}A</span>
        </span>
        <span className="text-slate-300">
          Peak: <span className="mono text-white font-medium">{peakCurrent.toFixed(1)}A</span>
        </span>
        <span className={imbalance > 5 ? 'text-amber-400' : 'text-slate-300'}>
          Imbalance: <span className={`mono font-medium ${imbalance > 5 ? 'text-amber-400' : 'text-white'}`}>{imbalance.toFixed(1)}%</span>
          {imbalance > 5 && ' ⚠️'}
        </span>
      </div>
    </div>
  )
}

// =====================================================
// Multi-Sensor Chart Component
// =====================================================
function MultiSensorChart({ data }) {
  const chartData = data.map((reading, index) => ({
    time: index,
    voltage: reading.voltage || 0,
    vibration: reading.vibration || 0,
    pressure: reading.pressure || 0,
    temperature: reading.temperature || 0,
  }))

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <Gauge className="w-5 h-5 text-cyan-400" />
        <h3 className="font-semibold text-white">📊 Sensor Trends (Last 60s)</h3>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Voltage Chart */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs text-slate-400">🔌 Voltage (V)</div>
            <div className="text-[11px] text-green-400">Plage OK: 220–240V (limite 210–250)</div>
          </div>
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="voltageGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.15)" />
                <XAxis dataKey="time" hide />
                <YAxis domain={[180, 260]} tick={{ fill: '#94a3b8', fontSize: 10 }} width={35} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(100, 116, 139, 0.3)', borderRadius: '6px' }}
                  formatter={(v) => [`${v.toFixed(1)} V`, 'Voltage']}
                />
                <ReferenceLine y={220} stroke="#64748b" strokeDasharray="3 3" />
                <ReferenceLine y={240} stroke="#64748b" strokeDasharray="3 3" />
                <ReferenceLine y={230} stroke="#64748b" strokeDasharray="3 3" />
                <Area type="monotone" dataKey="voltage" stroke="#a855f7" strokeWidth={2} fill="url(#voltageGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Vibration Chart */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs text-slate-400">📊 Vibration (mm/s)</div>
            <div className="text-[11px] text-green-400">Plage OK: ≤ 5 (limite 8)</div>
          </div>
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="vibrationGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.15)" />
                <XAxis dataKey="time" hide />
                <YAxis domain={[0, 15]} tick={{ fill: '#94a3b8', fontSize: 10 }} width={35} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(100, 116, 139, 0.3)', borderRadius: '6px' }}
                  formatter={(v) => [`${v.toFixed(2)} mm/s`, 'Vibration']}
                />
                <ReferenceArea y1={5} y2={15} fill="rgba(239, 68, 68, 0.1)" />
                <ReferenceLine y={5} stroke="#64748b" strokeDasharray="3 3" />
                <ReferenceLine y={8} stroke="#ef4444" strokeDasharray="3 3" />
                <Area type="monotone" dataKey="vibration" stroke="#f59e0b" strokeWidth={2} fill="url(#vibrationGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pressure Chart */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs text-slate-400">💨 Pressure (bar)</div>
            <div className="text-[11px] text-green-400">Plage OK: 3–6 bar (limite 2–7)</div>
          </div>
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="pressureGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.15)" />
                <XAxis dataKey="time" hide />
                <YAxis domain={[0, 8]} tick={{ fill: '#94a3b8', fontSize: 10 }} width={35} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(100, 116, 139, 0.3)', borderRadius: '6px' }}
                  formatter={(v) => [`${v.toFixed(2)} bar`, 'Pressure']}
                />
                <ReferenceLine y={3} stroke="#64748b" strokeDasharray="3 3" />
                <ReferenceLine y={6} stroke="#64748b" strokeDasharray="3 3" />
                <Area type="monotone" dataKey="pressure" stroke="#14b8a6" strokeWidth={2} fill="url(#pressureGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Temperature Chart */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs text-slate-400">🌡️ Temperature (°C)</div>
            <div className="text-[11px] text-green-400">Plage OK: ≤ 65°C (limite 80°C)</div>
          </div>
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.15)" />
                <XAxis dataKey="time" hide />
                <YAxis domain={[30, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }} width={35} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(100, 116, 139, 0.3)', borderRadius: '6px' }}
                  formatter={(v) => [`${v.toFixed(1)} °C`, 'Temperature']}
                />
                <ReferenceLine y={65} stroke="#64748b" strokeDasharray="3 3" />
                <ReferenceArea y1={80} y2={100} fill="rgba(239, 68, 68, 0.15)" />
                <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="3 3" />
                <Area type="monotone" dataKey="temperature" stroke="#ef4444" strokeWidth={2} fill="url(#tempGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

// =====================================================
// Main App Component
// =====================================================
function App() {
  // State
  const [connected, setConnected] = useState(false)
  const [sensorData, setSensorData] = useState(null)
  const [sensorHistory, setSensorHistory] = useState([])
  const [activeFault, setActiveFault] = useState('NORMAL')
  const [diagnosis, setDiagnosis] = useState('')
  const [diagnosisLoading, setDiagnosisLoading] = useState(false)
  const [shutdownDecision, setShutdownDecision] = useState(null)
  const [chatMessages, setChatMessages] = useState([])
  const [chatLoading, setChatLoading] = useState(false)
  const [faultTypes, setFaultTypes] = useState([])
  
  const wsRef = useRef(null)
  const sensorDataRef = useRef(null)  // Ref to always have latest sensor data
  const emergencyStopInProgressRef = useRef(false)

  // Chat session id stored in the browser (enables session-only memory on backend)
  const chatSessionIdRef = useRef(null)
  if (chatSessionIdRef.current === null) {
    try {
      const existing = window.localStorage.getItem('dt_chat_session_id')
      if (existing) {
        chatSessionIdRef.current = existing
      } else {
        const newId = (window.crypto && window.crypto.randomUUID)
          ? window.crypto.randomUUID()
          : `dt_${Date.now()}_${Math.random().toString(16).slice(2)}`
        window.localStorage.setItem('dt_chat_session_id', newId)
        chatSessionIdRef.current = newId
      }
    } catch {
      chatSessionIdRef.current = `dt_${Date.now()}_${Math.random().toString(16).slice(2)}`
    }
  }

  // Fetch fault types on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/fault-types`)
      .then(res => res.json())
      .then(data => setFaultTypes(data.fault_types))
      .catch(err => console.error('Failed to fetch fault types:', err))
  }, [])

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/sensor-stream`
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
      }
      
      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data)
        if (message.type === 'sensor_update') {
          setSensorData(message.data)
          sensorDataRef.current = message.data  // Keep ref updated
          setSensorHistory(prev => {
            const newHistory = [...prev, message.data]
            return newHistory.slice(-60)  // Keep last 60 readings
          })
          
          // Update active fault from sensor data
          if (message.data.fault_state) {
            const faultKey = message.data.fault_state.toUpperCase().replace(' ', '_')
            setActiveFault(faultKey === 'NORMAL' ? 'NORMAL' : faultKey)
          }
        }
      }
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000)
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }
    
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  // Diagnosis is manual: only run when the user clicks the Diagnose button.

  // Inject fault
  const handleInjectFault = async (faultId) => {
    try {
      const response = await fetch(`${API_BASE}/api/inject-fault`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fault_type: faultId })
      })
      
      if (response.ok) {
        setActiveFault(faultId)
        emergencyStopInProgressRef.current = false

        // Keep diagnosis manual; clear diagnosis when returning to normal.
        if (faultId === 'NORMAL') {
          setDiagnosis('')
          setShutdownDecision(null)
        }
      }
    } catch (error) {
      console.error('Failed to inject fault:', error)
    }
  }

  // Emergency stop function
  const handleEmergencyStop = async (reason) => {
    if (emergencyStopInProgressRef.current) return
    emergencyStopInProgressRef.current = true

    try {
      const response = await fetch(`${API_BASE}/api/emergency-stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        setActiveFault('NORMAL')

        // Clear any previous diagnosis/shutdown banner so the emergency button disappears.
        setShutdownDecision(null)
        setDiagnosis('')

        // Immediately reflect a stopped pump: zero-out sensor values in the UI.
        const zeroReading = {
          timestamp: new Date().toISOString(),
          fault_state: 'NORMAL',
          fault_duration: 0,
          amperage: {
            phase_a: 0,
            phase_b: 0,
            phase_c: 0,
            average: 0,
            imbalance_pct: 0,
          },
          voltage: 0,
          vibration: 0,
          pressure: 0,
          temperature: 0,
        }

        setSensorData(zeroReading)
        sensorDataRef.current = zeroReading
        setSensorHistory([zeroReading])
      }
    } catch (error) {
      console.error('Failed to execute emergency stop:', error)
    } finally {
      emergencyStopInProgressRef.current = false
    }
  }

  // Refresh diagnosis - uses ref to get latest sensor data
  const handleRefreshDiagnosis = async () => {
    const currentSensorData = sensorDataRef.current || sensorData
    if (!currentSensorData) return
    
    setDiagnosisLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensor_data: currentSensorData })
      })
      
      if (response.ok) {
        const data = await response.json()
        setDiagnosis(data.diagnosis)
        setShutdownDecision(data.shutdown_decision || null)
      } else {
        const error = await response.json()
        setDiagnosis(`Error: ${error.detail}`)
      }
    } catch (error) {
      setDiagnosis(`Connection error: ${error.message}`)
    } finally {
      setDiagnosisLoading(false)
    }
  }

  // Send chat message
  const handleSendMessage = async (message) => {
    setChatMessages(prev => [...prev, { role: 'user', content: message }])
    setChatLoading(true)
    
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message, 
          include_sensor_context: true,
          session_id: chatSessionIdRef.current,
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      } else {
        const error = await response.json()
        setChatMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `Sorry, I encountered an error: ${error.detail}` 
        }])
      }
    } catch (error) {
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Connection error: ${error.message}. Is the backend running?` 
      }])
    } finally {
      setChatLoading(false)
    }
  }

  // Get status based on sensor values
  const getMetricStatus = (type, value) => {
    if (!sensorData || activeFault === 'NORMAL') return 'normal'
    
    switch (type) {
      case 'amperage':
        if (sensorData.amperage?.imbalance_pct > 10) return 'danger'
        if (sensorData.amperage?.imbalance_pct > 5) return 'warning'
        return 'normal'
      case 'voltage':
        // Simulator publishes phase-to-neutral voltage (nominal ~230V)
        if (Math.abs(value - 230) > 20) return 'danger'
        if (Math.abs(value - 230) > 10) return 'warning'
        return 'normal'
      case 'vibration':
        if (value > 8) return 'danger'
        if (value > 5) return 'warning'
        return 'normal'
      case 'pressure':
        if (value < 2 || value > 7) return 'danger'
        if (value < 3 || value > 6) return 'warning'
        return 'normal'
      case 'temperature':
        if (value > 80) return 'danger'
        if (value > 65) return 'warning'
        return 'normal'
      default:
        return 'normal'
    }
  }

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <img src="/pump.svg" alt="Logo" className="w-10 h-10" />
            <div>
              <h1 className="text-2xl font-bold text-white">Digital Twin</h1>
              <p className="text-sm text-slate-400">Grundfos CR Pump • Predictive Maintenance</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <span className={`status-dot ${connected ? 'online' : 'offline'}`}></span>
          <span className={`text-sm ${connected ? 'text-green-400' : 'text-red-400'}`}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
          
          {activeFault !== 'NORMAL' && (
            <div className="flex items-center gap-2 ml-4 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/50">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-red-400 text-sm font-medium">
                {activeFault.replace('_', ' ')}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Main Layout: Full Width Dashboard */}
      <div className="flex gap-6">
        {/* Dashboard (Full Width) */}
        <div className="w-full space-y-6">
          {/* Top Row: 3D Model + Sensor Metrics */}
          <div className="flex gap-4">
            {/* 3D Pump Viewer */}
            <div className="w-[25%]">
              <div className="glass rounded-xl overflow-hidden h-[280px]">
                <div className="flex items-center gap-2 p-3 border-b border-slate-700/50">
                  <Box className="w-4 h-4 text-cyan-400" />
                  <h3 className="font-semibold text-white text-sm">3D Pump Model</h3>
                </div>
                <PumpViewer3D 
                  faultState={activeFault} 
                  sensorData={sensorData}
                  className="h-[240px]"
                />
              </div>
            </div>

            {/* Sensor Metrics with Sparklines */}
            <div className="w-[75%] grid grid-cols-3 gap-3">
              <MetricCard
                title="Amperage"
                value={sensorData?.amperage?.average || 0}
                unit="A"
                icon={Zap}
                status={getMetricStatus('amperage', sensorData?.amperage?.average)}
                subValues={[
                  { label: 'A', value: sensorData?.amperage?.phase_a?.toFixed(1) || '0', color: 'bg-red-400' },
                  { label: 'B', value: sensorData?.amperage?.phase_b?.toFixed(1) || '0', color: 'bg-green-400' },
                  { label: 'C', value: sensorData?.amperage?.phase_c?.toFixed(1) || '0', color: 'bg-blue-400' },
                ]}
                sparklineData={sensorHistory.slice(-30).map(d => ({ value: d.amperage?.average || 0 }))}
                threshold={sensorData?.amperage?.imbalance_pct > 5 ? `Imbalance: ${sensorData?.amperage?.imbalance_pct?.toFixed(1)}%` : 'Imbalance < 5%'}
              />
              <MetricCard
                title="Voltage"
                value={sensorData?.voltage || 0}
                unit="V"
                icon={Gauge}
                status={getMetricStatus('voltage', sensorData?.voltage)}
                sparklineData={sensorHistory.slice(-30).map(d => ({ value: d.voltage || 0 }))}
                threshold="Plage OK: 220–240V (limite 210–250)"
              />
              <MetricCard
                title="Vibration"
                value={sensorData?.vibration || 0}
                unit="mm/s"
                icon={Activity}
                status={getMetricStatus('vibration', sensorData?.vibration)}
                sparklineData={sensorHistory.slice(-30).map(d => ({ value: d.vibration || 0 }))}
                threshold="Plage OK: ≤ 5 (limite 8)"
              />
              <MetricCard
                title="Pressure"
                value={sensorData?.pressure || 0}
                unit="bar"
                icon={Droplets}
                status={getMetricStatus('pressure', sensorData?.pressure)}
                sparklineData={sensorHistory.slice(-30).map(d => ({ value: d.pressure || 0 }))}
                threshold="Plage OK: 3–6 bar (limite 2–7)"
              />
              <MetricCard
                title="Temperature"
                value={sensorData?.temperature || 0}
                unit="°C"
                icon={Thermometer}
                status={getMetricStatus('temperature', sensorData?.temperature)}
                sparklineData={sensorHistory.slice(-30).map(d => ({ value: d.temperature || 0 }))}
                threshold="Plage OK: ≤ 65°C (limite 80°C)"
              />
              <MetricCard
                title="Fault State"
                value={activeFault === 'NORMAL' ? 'OK' : activeFault.replace('_', ' ')}
                unit=""
                icon={activeFault === 'NORMAL' ? CheckCircle : AlertTriangle}
                status={activeFault === 'NORMAL' ? 'success' : 'danger'}
                sparklineData={[]}
                threshold={sensorData?.fault_duration ? `Duration: ${sensorData?.fault_duration?.toFixed(0)}s` : 'System Normal'}
              />
            </div>
          </div>

          {/* Live 3-Phase Chart */}
          <LiveChart data={sensorHistory} activeFault={activeFault} />

          {/* Multi-Sensor Trend Charts */}
          <MultiSensorChart data={sensorHistory} />

          {/* Fault Controls */}
          <div className="glass rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                <h3 className="font-semibold text-white">🧪 Fault Injection Controls (Development Mode)</h3>
              </div>
              {activeFault !== 'NORMAL' && (
                <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-red-500/20 border border-red-500/50">
                  <span className="text-red-400 text-sm">🚨 Active: {activeFault.replace('_', ' ')}</span>
                  <span className="text-red-300 text-xs">| Duration: {sensorData?.fault_duration?.toFixed(0) || 0}s</span>
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-6 gap-3">
              {faultTypes.map(ft => (
                <FaultButton
                  key={ft.id}
                  id={ft.id}
                  name={ft.name}
                  icon={ft.icon}
                  active={activeFault === ft.id}
                  onClick={handleInjectFault}
                  disabled={!connected}
                />
              ))}
            </div>
          </div>

          {/* AI Diagnosis */}
          <DiagnosisPanel
            diagnosis={diagnosis}
            shutdownDecision={shutdownDecision}
            isLoading={diagnosisLoading}
            onRefresh={handleRefreshDiagnosis}
            onEmergencyStop={handleEmergencyStop}
            activeFault={activeFault}
          />
        </div>
      </div>

      {/* Floating Chatbox */}
      <FloatingChatbox
        messages={chatMessages}
        onSendMessage={handleSendMessage}
        isLoading={chatLoading}
      />

      {/* Footer */}
      <footer className="mt-8 text-center text-slate-500 text-sm">
        <p>Digital Twin v1.0 • RAG-Enhanced Predictive Maintenance</p>
      </footer>
    </div>
  )
}

export default App
