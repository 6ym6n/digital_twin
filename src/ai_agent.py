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
- Structure responses: DIAGNOSIS → ROOT CAUSE → ACTION ITEMS
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
    
    def _build_diagnostic_query(self, sensor_data: Dict) -> str:
        """
        Construct a RAG query based on sensor anomalies.
        
        Args:
            sensor_data: Sensor readings dictionary
        
        Returns:
            Optimized query string for RAG retrieval
        """
        fault_state = sensor_data.get('fault_state', 'Normal')
        amps = sensor_data.get('amperage', {})
        imbalance = amps.get('imbalance_pct', 0)
        voltage = sensor_data.get('voltage', 230)
        vibration = sensor_data.get('vibration', 0)
        temperature = sensor_data.get('temperature', 65)
        
        # Build query based on detected anomalies
        query_parts = []
        
        if imbalance > 5:
            query_parts.append("motor winding defect phase imbalance")
        
        if voltage < 207:
            query_parts.append("voltage supply fault low voltage")
        
        if vibration > 5:
            query_parts.append("cavitation high vibration")
        
        if temperature > 80:
            query_parts.append("motor overheating causes")
        
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
        
        print("✅ Diagnostic complete!\n")
        
        return {
            "diagnosis": diagnosis_text,
            "context_used": retrieved_chunks,
            "rag_query": rag_query,
            "fault_detected": fault_detected,
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
    
    def ask_question(self, question: str, sensor_data: Optional[Dict] = None) -> str:
        """
        Chat mode - answer user questions about maintenance.
        
        Args:
            question: User's question
            sensor_data: Optional current sensor readings for context
        
        Returns:
            AI response text
        """
        print(f"\n💬 User Question: {question}")
        
        # Retrieve relevant documentation
        print("📚 Searching knowledge base...")
        chunks = self.rag_engine.query_knowledge_base(question, top_k=3)
        context = self._format_context(chunks)
        
        # Build prompt
        sensor_context = ""
        if sensor_data:
            sensor_context = f"\n\nCURRENT PUMP STATUS:\n{self._format_sensor_data(sensor_data)}"
        
        prompt = f"""{self.system_prompt}

{sensor_context}

DOCUMENTATION CONTEXT:
{context}

USER QUESTION: {question}

Provide a clear, actionable answer based on the manual and current pump status (if available)."""
        
        # Get response
        print("🤖 Generating response...")
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            response_text = response.content if response.content else "No response generated."
            
            if not response.content:
                print("⚠️  Warning: Empty response from model")
        except Exception as e:
            response_text = f"Error: {str(e)}"
            print(f"❌ Error: {str(e)}")
        
        print("✅ Response generated!\n")
        return response_text


# Testing and demonstration
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 AI AGENT TEST MODE")
    print("="*80 + "\n")
    
    try:
        # Initialize agent
        agent = MaintenanceAIAgent()
        
        # Import simulator for test data
        from simulator import PumpSimulator, FaultType
        pump = PumpSimulator()
        
        # Test scenarios
        test_scenarios = [
            (FaultType.WINDING_DEFECT, "Motor winding defect with phase imbalance"),
            (FaultType.CAVITATION, "Cavitation with high vibration"),
            (FaultType.SUPPLY_FAULT, "Voltage supply fault"),
        ]
        
        print("\n" + "─"*80)
        print("📋 RUNNING AUTO-DIAGNOSTIC TESTS")
        print("─"*80 + "\n")
        
        for fault_type, description in test_scenarios:
            print(f"\n{'═'*80}")
            print(f"🔧 TEST SCENARIO: {description}")
            print(f"{'═'*80}\n")
            
            # Inject fault and generate reading
            pump.inject_fault(fault_type)
            sensor_data = pump.get_sensor_reading()
            
            # Get AI diagnostic
            result = agent.get_diagnostic(sensor_data)
            
            print("🤖 AI DIAGNOSTIC:")
            print("─"*80)
            print(result['diagnosis'])
            print("─"*80)
            
            print(f"\n📚 Documentation References Used:")
            for i, chunk in enumerate(result['context_used'], 1):
                print(f"   [{i}] Page {chunk['page']} (Score: {chunk['score']:.3f})")
            
            input("\n⏸️  Press Enter to continue...\n")
        
        # Test chat mode
        print("\n" + "─"*80)
        print("💬 TESTING CHAT MODE")
        print("─"*80 + "\n")
        
        pump.reset_fault()
        sensor_data = pump.get_sensor_reading()
        
        test_questions = [
            "What tools do I need to inspect the impeller?",
            "How do I measure motor winding resistance?",
            "What causes mechanical seal failure?"
        ]
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            print("─"*80)
            answer = agent.ask_question(question, sensor_data)
            print(answer)
            print("─"*80)
            input("\n⏸️  Press Enter for next question...\n")
        
        print("\n" + "="*80)
        print("✅ AI AGENT TEST COMPLETE!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
