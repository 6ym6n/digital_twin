"""
Advanced RAG Engine Testing Suite
Tests retrieval quality and relevance for maintenance diagnostics
"""

from src.rag_engine import RAGEngine
import json

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_result(result: dict, index: int):
    """Print a single retrieval result with formatting"""
    print(f"\n{'─'*80}")
    print(f"📄 Result #{index}")
    print(f"{'─'*80}")
    print(f"📍 Page: {result['page']}")
    print(f"🎯 Relevance Score: {result['score']:.4f} (lower = more relevant)")
    print(f"\n📝 Content:\n{result['content']}")
    print(f"{'─'*80}")

def test_fault_scenarios():
    """Test real-world fault diagnosis scenarios"""
    
    print_section("🧪 FAULT DIAGNOSIS SCENARIOS")
    
    scenarios = [
        {
            "fault": "Motor Overheating",
            "sensor_data": "Motor temperature: 95°C, Amperage: 12.5A (rated 10A)",
            "question": "Motor is overheating and drawing excessive current. What are the possible causes?"
        },
        {
            "fault": "Voltage Imbalance",
            "sensor_data": "Phase A: 230V, Phase B: 220V, Phase C: 210V",
            "question": "Three-phase voltage readings show imbalance. How do I diagnose this?"
        },
        {
            "fault": "Cavitation",
            "sensor_data": "Vibration: 7.2 mm/s, Pressure fluctuating, Unusual noise",
            "question": "Pump showing high vibration and pressure fluctuations. Is this cavitation?"
        },
        {
            "fault": "Mechanical Seal Failure",
            "sensor_data": "Visible leakage, Temperature increase near seal",
            "question": "What causes mechanical seal failure in CR pumps?"
        },
        {
            "fault": "Low Flow Rate",
            "sensor_data": "Flow: 15 m³/h (expected 25 m³/h), Normal pressure",
            "question": "Pump delivering lower flow than expected. What should I check?"
        }
    ]
    
    rag = RAGEngine()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔧 SCENARIO {i}: {scenario['fault']}")
        print(f"📊 Sensor Data: {scenario['sensor_data']}")
        print(f"❓ Question: {scenario['question']}")
        
        results = rag.query_knowledge_base(scenario['question'], top_k=3)
        
        for j, result in enumerate(results, 1):
            print_result(result, j)
        
        # Ask user for feedback
        print("\n" + "─"*80)
        print("📊 QUALITY CHECK:")
        print("   Are these results relevant to the fault?")
        print("   Do they provide actionable diagnostic steps?")
        print("─"*80)
        
        input("\n⏸️  Press Enter to continue to next scenario...\n")

def test_specific_queries():
    """Test specific technical queries"""
    
    print_section("🔍 SPECIFIC TECHNICAL QUERIES")
    
    queries = [
        {
            "category": "Tools & Equipment",
            "query": "What tools are needed for pump disassembly?"
        },
        {
            "category": "Voltage Testing",
            "query": "How to measure and verify three-phase voltage?"
        },
        {
            "category": "Bearing Issues",
            "query": "Signs of bearing failure in centrifugal pump"
        },
        {
            "category": "Impeller Problems",
            "query": "How to inspect impeller for wear or damage?"
        },
        {
            "category": "Electrical Checks",
            "query": "Steps to test motor winding resistance"
        }
    ]
    
    rag = RAGEngine()
    
    for i, test in enumerate(queries, 1):
        print(f"\n📋 TEST {i}: {test['category']}")
        print(f"❓ Query: {test['query']}")
        
        results = rag.query_knowledge_base(test['query'], top_k=3)
        
        for j, result in enumerate(results, 1):
            print_result(result, j)
        
        print("\n" + "─"*80)
        print("💡 RELEVANCE CHECK:")
        print(f"   Does this answer the question about '{test['category']}'?")
        print("   Is the information specific and actionable?")
        print("─"*80)
        
        input("\n⏸️  Press Enter to continue...\n")

def test_context_quality():
    """Test the formatted context for LLM prompts"""
    
    print_section("📝 CONTEXT FORMATTING TEST (For LLM Prompts)")
    
    rag = RAGEngine()
    
    test_query = "Diagnose voltage imbalance causing motor winding damage"
    
    print(f"🔍 Query: {test_query}\n")
    
    # Get formatted context
    context = rag.get_context_for_prompt(test_query, top_k=3)
    
    print("📄 FORMATTED CONTEXT FOR LLM:")
    print("─"*80)
    print(context)
    print("─"*80)
    
    print("\n✅ This is what the AI agent will receive as context!")
    print("💡 Check if it contains enough detail for diagnosis.\n")

def test_edge_cases():
    """Test edge cases and unusual queries"""
    
    print_section("⚠️  EDGE CASE TESTING")
    
    edge_cases = [
        "What is the weather today?",  # Completely irrelevant
        "How to make coffee?",  # Off-topic
        "CR pump",  # Too vague
        "troubleshooting",  # Generic keyword
        "Page 8",  # Page reference only
    ]
    
    rag = RAGEngine()
    
    print("Testing how RAG handles irrelevant or vague queries...\n")
    
    for query in edge_cases:
        print(f"\n🧪 Query: '{query}'")
        results = rag.query_knowledge_base(query, top_k=2)
        
        print(f"📊 Results:")
        for i, result in enumerate(results, 1):
            print(f"   [{i}] Page {result['page']}, Score: {result['score']:.4f}")
            print(f"       Preview: {result['content'][:100]}...")
        
        print("\n   💭 Even irrelevant queries return something.")
        print("      This is why we need the LLM to filter and interpret!\n")

def compare_retrieval_strategies():
    """Compare different retrieval approaches"""
    
    print_section("⚖️  RETRIEVAL STRATEGY COMPARISON")
    
    rag = RAGEngine()
    
    test_query = "motor overheating causes"
    
    print(f"🔍 Query: '{test_query}'\n")
    
    # Test with different top_k values
    for k in [1, 3, 5]:
        print(f"\n📊 Retrieving Top-{k} Results:")
        print("─"*80)
        results = rag.query_knowledge_base(test_query, top_k=k)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Page {result['page']}, Score: {result['score']:.4f}")
            print(f"   {result['content'][:120]}...\n")
        
        print(f"💡 With Top-{k}: More results = more context but potential noise\n")

def main():
    """Run all tests with menu"""
    
    print("\n" + "🎯"*40)
    print("         RAG ENGINE QUALITY ASSURANCE SUITE")
    print("🎯"*40)
    
    tests = {
        "1": ("Fault Diagnosis Scenarios", test_fault_scenarios),
        "2": ("Specific Technical Queries", test_specific_queries),
        "3": ("Context Formatting for LLM", test_context_quality),
        "4": ("Edge Cases & Irrelevant Queries", test_edge_cases),
        "5": ("Compare Retrieval Strategies", compare_retrieval_strategies),
        "6": ("Run All Tests", None)
    }
    
    while True:
        print("\n" + "─"*80)
        print("📋 AVAILABLE TESTS:")
        print("─"*80)
        for key, (name, _) in tests.items():
            print(f"   {key}. {name}")
        print("   0. Exit")
        print("─"*80)
        
        choice = input("\n👉 Select test number (or 0 to exit): ").strip()
        
        if choice == "0":
            print("\n✅ Testing complete! Good luck with your Digital Twin! 🚀\n")
            break
        elif choice == "6":
            print("\n🚀 Running all tests...\n")
            for key, (name, func) in tests.items():
                if func and key != "6":
                    func()
        elif choice in tests and tests[choice][1]:
            tests[choice][1]()
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user.\n")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        raise
