import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  Activity, ChevronDown, ChevronRight,
  BookOpen, AlertCircle, Search, FileText
} from 'lucide-react';

/**
 * FaultTreeDiagram - Manual-based troubleshooting guide
 * Queries the Grundfos manual via RAG and displays the results
 */
const FaultTreeDiagram = ({ currentScenario, onPreventionClick }) => {
  const [manualData, setManualData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (currentScenario && currentScenario !== 'NORMAL') {
      fetchManualData(currentScenario);
    } else {
      setManualData(null);
    }
  }, [currentScenario]);

  const fetchManualData = async (scenarioId) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/manual-guide/${scenarioId}`);
      if (response.ok) {
        const data = await response.json();
        setManualData(data);
      }
    } catch (error) {
      console.error('Error fetching manual data:', error);
    }
    setLoading(false);
  };

  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 1: return { bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400', label: 'LOW' };
      case 2: return { bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400', label: 'MEDIUM' };
      case 3: return { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400', label: 'HIGH' };
      case 4: return { bg: 'bg-red-700/30', border: 'border-red-600', text: 'text-red-300', label: 'CRITICAL' };
      default: return { bg: 'bg-green-500/20', border: 'border-green-500/50', text: 'text-green-400', label: 'OK' };
    }
  };

  // Format manual content with better readability
  const formatManualContent = (content) => {
    if (!content) return null;
    
    // Split into paragraphs and format
    const paragraphs = content.split('\n\n').filter(p => p.trim());
    
    return paragraphs.map((paragraph, index) => {
      const trimmed = paragraph.trim();
      
      // Check if it's a header-like line (short, possibly capitalized)
      if (trimmed.length < 50 && (trimmed.toUpperCase() === trimmed || trimmed.endsWith(':'))) {
        return (
          <h4 key={index} className="font-semibold text-cyan-400 mt-4 mb-2">
            {trimmed}
          </h4>
        );
      }
      
      // Check if it's a bullet point or numbered list
      if (trimmed.match(/^[\-\•\*]\s/) || trimmed.match(/^\d+[\.\)]\s/)) {
        const items = trimmed.split('\n').filter(item => item.trim());
        return (
          <ul key={index} className="space-y-1 ml-4 mb-3">
            {items.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-slate-300 text-sm">
                <span className="text-cyan-400 mt-0.5">•</span>
                <span>{item.replace(/^[\-\•\*\d\.\)]\s*/, '')}</span>
              </li>
            ))}
          </ul>
        );
      }
      
      // Regular paragraph
      return (
        <p key={index} className="text-slate-300 text-sm mb-3 leading-relaxed">
          {trimmed}
        </p>
      );
    });
  };

  if (!currentScenario || currentScenario === 'NORMAL') {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-400" />
          Manual Reference
        </h3>
        <div className="text-center py-8 text-slate-500">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500/50" />
          <p>System is in normal state</p>
          <p className="text-sm mt-1">Inject a fault to query the Grundfos manual</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-400" />
          Manual Reference
        </h3>
        <div className="text-center py-8">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 mt-3">Querying Grundfos manual...</p>
          <p className="text-slate-500 text-xs mt-1">Searching documentation via RAG</p>
        </div>
      </div>
    );
  }

  if (!manualData) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-400" />
          Manual Reference
        </h3>
        <div className="text-center py-8 text-slate-500">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 text-slate-500/50" />
          <p>No manual data found for this fault</p>
        </div>
      </div>
    );
  }

  const severityStyle = getSeverityStyle(manualData.severity);

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      {/* Header */}
      <h3 className="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-blue-400" />
        Manual Reference
        <span className="text-xs text-slate-500 font-normal ml-2">(RAG Query Results)</span>
      </h3>

      {/* Fault Header */}
      <div className={`p-4 rounded-lg ${severityStyle.bg} border ${severityStyle.border} mb-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{manualData.icon}</span>
            <div>
              <div className={`text-lg font-bold ${severityStyle.text}`}>{manualData.name}</div>
              <div className="text-sm text-slate-400">{manualData.description}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Query Info */}
      {manualData.query_used && (
        <div className="mb-4 p-2 bg-slate-900/50 rounded border border-slate-700">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Search className="w-3 h-3" />
            <span>RAG Query: "{manualData.query_used}"</span>
          </div>
        </div>
      )}

      {/* Manual Content */}
      <div 
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between p-3 bg-cyan-900/20 border border-cyan-500/30 rounded-lg">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            <span className="font-semibold text-cyan-400">Manual Content</span>
            <span className="text-xs text-slate-500">(from Grundfos PDF)</span>
          </div>
          {expanded ? (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </div>

      {expanded && manualData.manual_content && (
        <div className="mt-2 p-4 bg-slate-900/50 rounded-lg border-l-4 border-cyan-500 max-h-96 overflow-y-auto">
          {formatManualContent(manualData.manual_content)}
        </div>
      )}

      {/* Manual References */}
      {manualData.manual_references && manualData.manual_references.length > 0 && (
        <div className="mt-4 p-3 bg-slate-900/70 rounded-lg border border-slate-600">
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
            <BookOpen className="w-4 h-4" />
            <span className="font-semibold">Sources from Manual:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {manualData.manual_references.map((ref, index) => (
              <span key={index} className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                📖 {ref}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Error state */}
      {manualData.error && (
        <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
          <p className="text-red-400 text-sm">{manualData.error}</p>
        </div>
      )}
    </div>
  );
};

export default FaultTreeDiagram;
