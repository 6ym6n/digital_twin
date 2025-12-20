"""
AI Agent for Predictive Maintenance Diagnostics
Integrates Google Gemini with RAG for intelligent fault analysis
"""

import os
import sys
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rag_engine import RAGEngine

# Load environment variables
load_dotenv()


class MaintenanceAIAgent:
    """
    AI-powered diagnostic agent for pump troubleshooting.
    Combines real-time sensor data with RAG-retrieved documentation.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 1000000
    ):
        """
        Initialize the AI agent with Gemini LLM and RAG engine.
        
        Args:
            model_name: Gemini model to use (default: gemini-2.5-flash for low latency)
            temperature: Creativity vs consistency (0.0-1.0, lower = more focused)
            max_tokens: Maximum response length
        """
        # Verify API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables!")
        
        # Initialize Gemini LLM
        print("🤖 Initializing Google Gemini AI Agent...")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
            convert_system_message_to_human=True  # Gemini compatibility
        )
        
        # Initialize RAG engine
        print("📚 Connecting to knowledge base...")
        self.rag_engine = RAGEngine()
        
        # System prompt for maintenance engineer persona
        self.system_prompt = self._create_system_prompt()
        
        print("✅ AI Agent initialized successfully!")
        print(f"   Model: {model_name}")
        print(f"   Temperature: {temperature}")
        print(f"   Max Tokens: {max_tokens}\n")
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt that defines AI behavior.
        
        Returns:
            System prompt string
        """
        return """You are a Senior Maintenance Engineer specialized in Grundfos CR centrifugal pumps with 15+ years of experience in industrial diagnostics.

Your responsibilities:
1. Analyze sensor data to identify root causes of pump failures
2. Provide actionable diagnostic steps based on manufacturer documentation
3. Recommend specific tools, measurements, and corrective actions
4. Prioritize safety and equipment protection
5. Keep explanations concise for real-time dashboard display

Communication style:
- Use technical terminology but remain clear
- For full diagnosis reports, structure responses: DIAGNOSIS → ROOT CAUSE → ACTION ITEMS
- For chat Q&A, answer the user's question directly without repeating a full report unless asked
- Reference specific manual pages when applicable
- If unsure, recommend additional measurements rather than guessing
- For emergencies (extreme values), recommend immediate shutdown

Context awareness:
- You receive real-time sensor readings (amperage, voltage, vibration, etc.)
- You have access to the Grundfos CR pump troubleshooting manual via RAG
- Historical fault patterns help identify progressive failures
"""
    
    def _format_sensor_data(self, sensor_data: Dict) -> str:
        """
        Format sensor readings into human-readable text for the prompt.
        
        Args:
            sensor_data: Dictionary from PumpSimulator.get_sensor_reading()
        
        Returns:
            Formatted sensor data string
        """
        amps = sensor_data.get('amperage', {})
        
        sensor_text = f"""Current Sensor Readings:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• TIMESTAMP: {sensor_data.get('timestamp', 'N/A')}
• FAULT STATE: {sensor_data.get('fault_state', 'Unknown')}
• FAULT DURATION: {sensor_data.get('fault_duration', 0)} seconds

ELECTRICAL:
  - Phase A Current: {amps.get('phase_a', 'N/A')} A
  - Phase B Current: {amps.get('phase_b', 'N/A')} A
  - Phase C Current: {amps.get('phase_c', 'N/A')} A
  - Average Current: {amps.get('average', 'N/A')} A
  - Phase Imbalance: {amps.get('imbalance_pct', 'N/A')}%
  - Supply Voltage: {sensor_data.get('voltage', 'N/A')} V

MECHANICAL:
  - Vibration: {sensor_data.get('vibration', 'N/A')} mm/s
  - Discharge Pressure: {sensor_data.get('pressure', 'N/A')} bar
  
THERMAL:
  - Motor Temperature: {sensor_data.get('temperature', 'N/A')} °C
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return sensor_text
    
    def _evaluate_shutdown_decision(self, sensor_data: Dict) -> Dict[str, any]:
        """
        Evaluate whether the pump should be stopped based on sensor readings.
        
        Based on Grundfos manual recommendations:
        - Page 5: "Do NOT stop the pump immediately" for initial diagnosis
        - Critical conditions require immediate shutdown
        
        Thresholds:
        - Imbalance > 5%: From Grundfos manual Page 7
        - Voltage ±10%: From Grundfos manual Page 8
        - Vibration > 5 mm/s: ISO 10816 standard for pumps
        - Temperature > 80°C: IEC Class B motor insulation limit
        
        Args:
            sensor_data: Current sensor readings
            
        Returns:
            Dictionary with shutdown decision and reasoning
        """
        amps = sensor_data.get('amperage', {})
        imbalance = amps.get('imbalance_pct', 0)
        voltage = sensor_data.get('voltage', 230)
        vibration = sensor_data.get('vibration', 0)
        temperature = sensor_data.get('temperature', 65)
        pressure = sensor_data.get('pressure', 4)
        
        # Critical thresholds - IMMEDIATE SHUTDOWN REQUIRED
        critical_conditions = []
        
        # Temperature > 90°C: Imminent motor damage
        if temperature > 90:
            critical_conditions.append({
                "parameter": "Temperature",
                "value": f"{temperature:.1f}°C",
                "threshold": "90°C",
                "reason": "Motor insulation damage imminent - risk of fire"
            })
        
        # Extreme vibration > 10 mm/s: Mechanical destruction
        if vibration > 10:
            critical_conditions.append({
                "parameter": "Vibration",
                "value": f"{vibration:.2f} mm/s",
                "threshold": "10 mm/s",
                "reason": "Severe mechanical damage in progress - bearing/impeller destruction"
            })
        
        # Severe phase imbalance > 15%: Winding burnout risk
        if imbalance > 15:
            critical_conditions.append({
                "parameter": "Phase Imbalance",
                "value": f"{imbalance:.1f}%",
                "threshold": "15%",
                "reason": "Severe winding damage risk - motor burnout imminent"
            })
        
        # Voltage < 180V or > 270V (>20% deviation): Motor damage
        if voltage < 180 or voltage > 270:
            critical_conditions.append({
                "parameter": "Voltage",
                "value": f"{voltage:.1f}V",
                "threshold": "180-270V (±20%)",
                "reason": "Extreme voltage - immediate motor protection required"
            })
        
        # Zero or negative pressure: Dry running
        if pressure <= 0:
            critical_conditions.append({
                "parameter": "Pressure",
                "value": f"{pressure:.2f} bar",
                "threshold": "> 0 bar",
                "reason": "Dry running detected - pump damage imminent"
            })
        
        # Warning thresholds - Continue for diagnosis, then decide
        warning_conditions = []
        
        # Temperature 80-90°C: Monitor closely
        if 80 <= temperature <= 90:
            warning_conditions.append({
                "parameter": "Temperature",
                "value": f"{temperature:.1f}°C",
                "threshold": "80°C",
                "reason": "Elevated temperature - monitor and diagnose cause"
            })
        
        # Vibration 5-10 mm/s: Needs attention
        if 5 < vibration <= 10:
            warning_conditions.append({
                "parameter": "Vibration",
                "value": f"{vibration:.2f} mm/s",
                "threshold": "5 mm/s",
                "reason": "High vibration - continue briefly for diagnosis"
            })
        
        # Phase imbalance 5-15%: Investigate
        if 5 < imbalance <= 15:
            warning_conditions.append({
                "parameter": "Phase Imbalance",
                "value": f"{imbalance:.1f}%",
                "threshold": "5%",
                "reason": "Current imbalance detected - check windings after diagnosis"
            })
        
        # Voltage deviation 10-20%: Poor supply
        if (180 <= voltage < 207) or (253 < voltage <= 270):
            warning_conditions.append({
                "parameter": "Voltage",
                "value": f"{voltage:.1f}V",
                "threshold": "±10% (207-253V)",
                "reason": "Voltage out of tolerance - contact power supplier"
            })
        
        # Low pressure: Possible cavitation
        if 0 < pressure < 2:
            warning_conditions.append({
                "parameter": "Pressure",
                "value": f"{pressure:.2f} bar",
                "threshold": "2 bar",
                "reason": "Low pressure - check for cavitation or blockage"
            })
        
        # Determine shutdown decision
        if critical_conditions:
            return {
                "action": "IMMEDIATE_SHUTDOWN",
                "urgency": "CRITICAL",
                "icon": "⛔",
                "message": "ARRÊT IMMÉDIAT REQUIS - Conditions critiques détectées",
                "message_en": "IMMEDIATE SHUTDOWN REQUIRED - Critical conditions detected",
                "critical_conditions": critical_conditions,
                "warning_conditions": warning_conditions,
                "recommendation": "Couper l'alimentation immédiatement. Ne pas redémarrer avant inspection complète.",
                "recommendation_en": "Cut power immediately. Do not restart before complete inspection."
            }
        elif warning_conditions:
            return {
                "action": "CONTINUE_THEN_STOP",
                "urgency": "WARNING",
                "icon": "⚠️",
                "message": "Continuer pour diagnostic, puis arrêter pour inspection",
                "message_en": "Continue for diagnosis, then stop for inspection",
                "critical_conditions": [],
                "warning_conditions": warning_conditions,
                "recommendation": "Comme recommandé par Grundfos (Page 5): Ne pas arrêter immédiatement. Effectuer les mesures pendant le fonctionnement, puis arrêter pour correction.",
                "recommendation_en": "As recommended by Grundfos (Page 5): Do NOT stop immediately. Take measurements while running, then stop for correction."
            }
        else:
            return {
                "action": "NORMAL_OPERATION",
                "urgency": "OK",
                "icon": "✅",
                "message": "Fonctionnement normal - Aucune action requise",
                "message_en": "Normal operation - No action required",
                "critical_conditions": [],
                "warning_conditions": [],
                "recommendation": "Continuer la surveillance normale.",
                "recommendation_en": "Continue normal monitoring."
            }
    
    def _build_diagnostic_query(self, sensor_data: Dict) -> str:
        """
        Construct a RAG query based on sensor anomalies.
        
        Args:
            sensor_data: Sensor readings dictionary
        
        Returns:
            Optimized query string for RAG retrieval
            
        Threshold Sources:
        - Imbalance > 5%: Grundfos Manual Page 7
        - Voltage < 207V (10% of 230V): Grundfos Manual Page 8
        - Vibration > 5 mm/s: ISO 10816 industrial standard
        - Vibration 3-5 mm/s: ISO 10816 warning zone
        - Temperature > 80°C: IEC Class B insulation standard
        """
        fault_state = sensor_data.get('fault_state', 'Normal')
        amps = sensor_data.get('amperage', {})
        imbalance = amps.get('imbalance_pct', 0)
        voltage = sensor_data.get('voltage', 230)
        vibration = sensor_data.get('vibration', 0)
        temperature = sensor_data.get('temperature', 65)
        
        # Build query based on detected anomalies
        query_parts = []
        
        # Grundfos Manual Page 7: "If the current imbalance does not exceed 5%"
        if imbalance > 5:
            query_parts.append("motor winding defect phase imbalance")
        
        # Grundfos Manual Page 8: "voltage should be within 10% (+ or -)"
        if voltage < 207:
            query_parts.append("voltage supply fault low voltage")
        
        # ISO 10816: Vibration > 5 mm/s = unacceptable for pumps
        if vibration > 5:
            query_parts.append("cavitation high vibration")
        
        # IEC Class B insulation: Max operating temp 80°C
        if temperature > 80:
            query_parts.append("motor overheating causes")
        
        # ISO 10816: Vibration 3-5 mm/s = alert zone
        if vibration > 3 and vibration <= 5:
            query_parts.append("bearing wear diagnosis")
        
        # If no specific anomalies, use fault state
        if not query_parts:
            query_parts.append(f"{fault_state} troubleshooting diagnosis")
        
        return " ".join(query_parts)
    
    def get_diagnostic(
        self,
        sensor_data: Dict,
        user_question: Optional[str] = None,
        include_context: bool = True
    ) -> Dict[str, any]:
        """
        Generate AI diagnostic response based on sensor data.
        
        Args:
            sensor_data: Current sensor readings from PumpSimulator
            user_question: Optional user query (for chat mode)
            include_context: Whether to retrieve RAG context
        
        Returns:
            Dictionary containing:
                - diagnosis: AI response text
                - context_used: Retrieved documentation chunks
                - query: RAG query that was used
                - fault_detected: Boolean
        """
        print(f"\n🔍 Analyzing fault: {sensor_data.get('fault_state', 'Unknown')}")
        
        # Format sensor data
        sensor_text = self._format_sensor_data(sensor_data)
        
        # Retrieve relevant documentation
        context = ""
        retrieved_chunks = []
        rag_query = ""
        
        if include_context:
            rag_query = self._build_diagnostic_query(sensor_data)
            print(f"📚 RAG Query: '{rag_query}'")
            
            retrieved_chunks = self.rag_engine.query_knowledge_base(
                query=rag_query,
                top_k=3
            )
            
            context = self._format_context(retrieved_chunks)
        
        # Build the prompt
        if user_question:
            # Chat mode - user asked a specific question
            prompt = f"""{self.system_prompt}

{sensor_text}

DOCUMENTATION CONTEXT:
{context if context else "No specific documentation retrieved."}

USER QUESTION: {user_question}

Provide a focused answer to the user's question using the sensor data and documentation."""
        else:
            # Auto-diagnostic mode - analyze fault automatically
            prompt = f"""{self.system_prompt}

{sensor_text}

DOCUMENTATION CONTEXT:
{context if context else "No specific documentation retrieved."}

TASK: Analyze the sensor readings above and provide:
1. PRIMARY DIAGNOSIS: What is the most likely fault?
2. ROOT CAUSE: Why is this happening?
3. IMMEDIATE ACTIONS: What should the technician do now?
4. VERIFICATION STEPS: How to confirm the diagnosis?

Keep your response under 300 words for dashboard display."""
        
        # Get AI response
        print("🤖 Generating diagnostic response...")
        
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            diagnosis_text = response.content if response.content else "No response generated. The model may have filtered the content."
            
            # Debug: Check for safety ratings or other issues
            if not response.content:
                print("⚠️  Warning: Empty response from model")
                if hasattr(response, 'response_metadata'):
                    print(f"Response metadata: {response.response_metadata}")
        
        except Exception as e:
            diagnosis_text = f"Error generating diagnosis: {str(e)}"
            print(f"❌ Error: {str(e)}")
        
        # Detect if this is an actual fault
        fault_detected = sensor_data.get('fault_state', 'Normal') != 'Normal'
        
        # Evaluate shutdown decision based on Grundfos manual recommendations
        shutdown_decision = self._evaluate_shutdown_decision(sensor_data)
        
        # Log shutdown decision
        if shutdown_decision["action"] == "IMMEDIATE_SHUTDOWN":
            print(f"⛔ CRITICAL: {shutdown_decision['message_en']}")
            for cond in shutdown_decision["critical_conditions"]:
                print(f"   - {cond['parameter']}: {cond['value']} (threshold: {cond['threshold']})")
        elif shutdown_decision["action"] == "CONTINUE_THEN_STOP":
            print(f"⚠️  WARNING: {shutdown_decision['message_en']}")
        
        print("✅ Diagnostic complete!\n")
        
        return {
            "diagnosis": diagnosis_text,
            "context_used": retrieved_chunks,
            "rag_query": rag_query,
            "fault_detected": fault_detected,
            "shutdown_decision": shutdown_decision,
            "sensor_summary": {
                "fault_state": sensor_data.get('fault_state'),
                "imbalance": sensor_data.get('amperage', {}).get('imbalance_pct'),
                "voltage": sensor_data.get('voltage'),
                "vibration": sensor_data.get('vibration'),
                "temperature": sensor_data.get('temperature')
            }
        }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved documentation chunks for the prompt.
        
        Args:
            chunks: List of retrieved document chunks from RAG
        
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant documentation found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            page = chunk.get('page', 'Unknown')
            content = chunk.get('content', '')
            context_parts.append(
                f"[Manual Reference {i} - Page {page}]\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    def ask_question(
        self,
        question: str,
        sensor_data: Optional[Dict] = None,
        fault_context: Optional[Dict] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Chat mode - answer user questions about maintenance.
        
        Args:
            question: User's question
            sensor_data: Optional current sensor readings for context
        
        Returns:
            AI response text
        """
        print(f"\n💬 User Question: {question}")

        # Session-only memory: keep a small rolling chat history in the prompt.
        history_text = ""
        if chat_history and isinstance(chat_history, list):
            # Keep only last 8 messages to avoid bloating the prompt.
            trimmed = chat_history[-8:]
            lines = []
            for m in trimmed:
                role = (m.get("role") or "").strip().lower()
                content = (m.get("content") or "").strip()
                if not content:
                    continue
                label = "User" if role == "user" else "Assistant"
                lines.append(f"{label}: {content}")
            history_text = "\n".join(lines).strip()
        
        # Retrieve relevant documentation
        print("📚 Searching knowledge base...")
        chunks = self.rag_engine.query_knowledge_base(question, top_k=3)
        context = self._format_context(chunks)
        
        # Build prompt
        sensor_context = ""
        shutdown_context = ""
        fault_start_context = ""
        if sensor_data:
            sensor_context = f"\n\nCURRENT PUMP STATUS:\n{self._format_sensor_data(sensor_data)}"
            try:
                shutdown = self._evaluate_shutdown_decision(sensor_data)
                shutdown_context = (
                    "\n\nSAFETY EVALUATION (computed from thresholds):\n"
                    f"- action: {shutdown.get('action')}\n"
                    f"- urgency: {shutdown.get('urgency')}\n"
                    f"- message: {shutdown.get('message_en') or shutdown.get('message') or ''}"
                )
            except Exception:
                shutdown_context = ""

        if fault_context and isinstance(fault_context, dict):
            start_snapshot = fault_context.get("fault_start_snapshot")
            start_seen_at = fault_context.get("fault_start_seen_at")
            start_estimated_at = fault_context.get("fault_start_estimated_at")
            start_fault_state = fault_context.get("fault_state")
            if start_snapshot and isinstance(start_snapshot, dict):
                when = start_estimated_at or start_seen_at
                when_line = f"Timestamp: {when}" if when else "Timestamp: unknown"
                fault_line = f"Fault: {start_fault_state}" if start_fault_state else "Fault: unknown"
                fault_start_context = (
                    "\n\nFAULT START SNAPSHOT (captured by backend):\n"
                    f"{fault_line}\n"
                    f"{when_line}\n"
                    f"{self._format_sensor_data(start_snapshot)}"
                )
        
        prompt = f"""{self.system_prompt}

    CHAT MODE INSTRUCTIONS (must follow):
    - Reply in the same language as the user's question.
    - Give a DIRECT answer to the user's question (what to do / how to fix).
    - Do NOT output headings like: DIAGNOSIS, ROOT CAUSE, ACTION ITEMS, VERIFICATION STEPS.
    - Keep it short: 4–8 bullet points maximum.
    - If the safety evaluation indicates IMMEDIATE_SHUTDOWN, the first bullet must say to stop immediately.
    - Only include the 1–2 most relevant verification checks.
    - If the user asks about the *beginning* of the fault (e.g. "au début"), use the FAULT START SNAPSHOT if provided.
    - If no start snapshot is provided, say you don't have it and give the closest available info.
    - Use CHAT HISTORY if it helps keep context within this session.

    {sensor_context}{shutdown_context}{fault_start_context}

    CHAT HISTORY (this session, most recent):
    {history_text if history_text else "(none)"}

    DOCUMENTATION CONTEXT:
    {context}

    USER QUESTION: {question}
    """
        
        # Get response
        print("🤖 Generating response...")
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            response_text = response.content if response.content else "No response generated."
            response_text = self._postprocess_chat_response(question, response_text)
            
            if not response.content:
                print("⚠️  Warning: Empty response from model")
        except Exception as e:
            response_text = f"Error: {str(e)}"
            print(f"❌ Error: {str(e)}")
        
        print("✅ Response generated!\n")
        return response_text

    def generate_logigramme(
        self,
        fault_type: str,
        sensor_data: Optional[Dict] = None,
        diagnosis_text: Optional[str] = None,
    ) -> List[Dict[str, any]]:
        """
        Generate a dynamic logigramme (flowchart steps) for the technician.
        Uses RAG to retrieve relevant manual sections and LLM to generate steps.
        
        Args:
            fault_type: The current fault type (e.g., 'WINDING_DEFECT')
            sensor_data: Optional current sensor readings
            diagnosis_text: Optional diagnosis text for additional context
        
        Returns:
            List of step dictionaries with id, label, icon, critical flag
        """
        print(f"\n📋 Generating logigramme for fault: {fault_type}")
        
        # Build RAG query based on fault type
        fault_queries = {
            "WINDING_DEFECT": "motor winding defect repair steps troubleshooting procedure",
            "SUPPLY_FAULT": "voltage supply fault electrical troubleshooting procedure",
            "CAVITATION": "pump cavitation repair steps NPSH troubleshooting procedure",
            "BEARING_WEAR": "bearing wear replacement lubrication troubleshooting procedure",
            "OVERLOAD": "motor overload protection troubleshooting procedure",
        }
        
        rag_query = fault_queries.get(fault_type, f"{fault_type} troubleshooting repair procedure")
        
        # Retrieve relevant documentation
        print("📚 Searching knowledge base for procedures...")
        chunks = self.rag_engine.query_knowledge_base(rag_query, top_k=4)
        context = self._format_context(chunks)
        
        # Build sensor context if available
        sensor_context = ""
        if sensor_data:
            sensor_context = f"\n\nCURRENT SENSOR READINGS:\n{self._format_sensor_data(sensor_data)}"
        
        # Build diagnosis context
        diagnosis_context = ""
        if diagnosis_text:
            diagnosis_context = f"\n\nAI DIAGNOSIS:\n{diagnosis_text[:500]}..."
        
        # Prompt for generating structured steps
        prompt = f"""You are a Senior Maintenance Engineer creating a step-by-step troubleshooting flowchart for a technician.

FAULT TYPE: {fault_type.replace('_', ' ')}
{sensor_context}
{diagnosis_context}

RELEVANT DOCUMENTATION FROM GRUNDFOS MANUAL:
{context}

TASK: Generate 5-7 actionable steps for the technician to diagnose and fix this fault.

RULES:
- Each step must be a single clear action (start with a verb)
- Mark steps that are CRITICAL for safety with [CRITICAL] prefix
- Steps should follow logical order: safety first, then diagnosis, then repair
- Reference specific tools, measurements, or thresholds from the manual when possible
- Keep each step under 10 words
- Use English only

FORMAT: Return ONLY a numbered list like this:
1. [CRITICAL] Cut power supply immediately
2. Check motor temperature with thermometer
3. Measure winding resistance with multimeter
...

Do not add any introduction or conclusion. Just the numbered list."""
        
        # Get LLM response
        print("🤖 Generating steps...")
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            response_text = response.content if response.content else ""
        except Exception as e:
            print(f"❌ Error generating logigramme: {str(e)}")
            return self._get_fallback_logigramme(fault_type)
        
        # Parse the response into structured steps
        steps = self._parse_logigramme_response(response_text)
        
        if not steps:
            print("⚠️ No steps parsed, using fallback")
            return self._get_fallback_logigramme(fault_type)
        
        print(f"✅ Generated {len(steps)} steps\n")
        return steps
    
    def _parse_logigramme_response(self, response_text: str) -> List[Dict[str, any]]:
        """
        Parse LLM response into structured step objects.
        """
        steps = []
        lines = response_text.strip().split('\n')
        
        # Icon mapping based on keywords
        icon_map = {
            'power': '⚡', 'cut': '⚡', 'voltage': '⚡', 'electrical': '⚡',
            'temperature': '🌡️', 'heat': '🌡️', 'thermal': '🌡️', 'cool': '❄️',
            'measure': '📊', 'check': '🔍', 'inspect': '👁️', 'test': '📊',
            'resistance': '🔧', 'winding': '🔧', 'replace': '🔄', 'repair': '🔧',
            'bearing': '⚙️', 'lubricate': '🛢️', 'oil': '🛢️',
            'vibration': '📳', 'pressure': '📏', 'flow': '💧', 'level': '📏',
            'filter': '🔍', 'clean': '🧹', 'remove': '🔧',
            'listen': '👂', 'sound': '👂', 'noise': '👂',
            'restart': '▶️', 'start': '▶️', 'stop': '⏹️',
            'document': '📝', 'record': '📝', 'log': '📝',
            'contact': '📞', 'call': '📞',
        }
        
        step_id = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match numbered lines: "1. Step text" or "1) Step text"
            import re
            match = re.match(r'^\d+[\.\)]\s*(.+)$', line)
            if match:
                step_id += 1
                step_text = match.group(1).strip()
                
                # Check if critical
                is_critical = '[CRITICAL]' in step_text.upper() or '[critical]' in step_text
                step_text = re.sub(r'\[CRITICAL\]\s*', '', step_text, flags=re.IGNORECASE).strip()
                
                # Find appropriate icon
                icon = '🔧'  # default
                step_lower = step_text.lower()
                for keyword, emoji in icon_map.items():
                    if keyword in step_lower:
                        icon = emoji
                        break
                
                steps.append({
                    'id': step_id,
                    'label': step_text,
                    'icon': icon,
                    'critical': is_critical,
                })
        
        return steps
    
    def _get_fallback_logigramme(self, fault_type: str) -> List[Dict[str, any]]:
        """
        Return basic fallback steps if LLM fails.
        """
        base_steps = [
            {'id': 1, 'label': 'Cut power supply', 'icon': '⚡', 'critical': True},
            {'id': 2, 'label': 'Verify safe working conditions', 'icon': '🔍', 'critical': True},
            {'id': 3, 'label': 'Inspect affected component', 'icon': '👁️', 'critical': False},
            {'id': 4, 'label': 'Take measurements', 'icon': '📊', 'critical': False},
            {'id': 5, 'label': 'Repair or replace faulty part', 'icon': '🔧', 'critical': False},
            {'id': 6, 'label': 'Test operation before restart', 'icon': '📊', 'critical': False},
        ]
        return base_steps

    def _postprocess_chat_response(self, question: str, response_text: str) -> str:
        value = (response_text or "").strip()
        if not value:
            return ""

        upper = value.upper()
        has_report_headers = any(
            key in upper
            for key in ("DIAGNOSIS", "ROOT CAUSE", "ACTION ITEMS", "IMMEDIATE ACTIONS", "VERIFICATION STEPS")
        )
        if not has_report_headers:
            return value

        # Extract the ACTION ITEMS / IMMEDIATE ACTIONS section if present.
        lines = value.splitlines()
        header_regex = r"^(?:#+\s*)?(?:\*\*)?\s*(DIAGNOSIS|ROOT\s*CAUSE|ACTION\s*ITEMS?|IMMEDIATE\s*ACTIONS?|VERIFICATION\s*STEPS?|RECOMMENDATION)\s*(?:\*\*)?\s*:?.*$"

        section = None
        sections = {
            "action": [],
            "verification": [],
            "other": [],
        }

        import re

        for raw in lines:
            line = str(raw).rstrip()
            m = re.match(header_regex, line.strip(), flags=re.IGNORECASE)
            if m:
                key = m.group(1).strip().upper()
                if "ACTION" in key:
                    section = "action"
                elif "VERIFICATION" in key:
                    section = "verification"
                else:
                    section = "other"
                continue

            if section is None:
                continue
            sections[section].append(line)

        def extract_bullets(section_lines):
            text = "\n".join(section_lines)
            out = []
            for raw_line in text.splitlines():
                s = raw_line.strip()
                if not s:
                    continue
                s = re.sub(r"^\s*(?:\d+\.|\-|\*|•)\s+", "", s)
                if s:
                    out.append(s)
            return out

        action = extract_bullets(sections["action"])[:8]
        verification = extract_bullets(sections["verification"])[:2]

        # If we couldn't extract anything, return the original.
        if not action and not verification:
            return value

        q_upper = (question or "").upper()
        french = any(tok in q_upper for tok in ("QUE ", "QU'", "QUOI", "COMMENT", "POURQUOI", "RÉGLER", "REGLER"))
        title = "À faire maintenant:" if french else "What to do now:"

        parts = [title]
        for item in action:
            parts.append(f"- {item}")
        for item in verification:
            parts.append(f"- {item}")

        return "\n".join(parts).strip()


# Testing and demonstration
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 AI AGENT TEST MODE")
    print("="*80 + "\n")
    print("Note: This test mode requires MATLAB simulation to be running with MQTT.")
    print("      The Python simulator has been removed.")
    print("      Please use the full system with backend/api.py instead.")
    print("="*80 + "\n")
