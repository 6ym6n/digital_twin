"""
Simple test script for AI Agent with proper encoding
Run this instead of directly running ai_agent.py
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai_agent import MaintenanceAIAgent
from src.simulator import PumpSimulator, FaultType

print("\n" + "="*80)
print("🧪 AI AGENT QUICK TEST")
print("="*80 + "\n")

# Initialize
agent = MaintenanceAIAgent()
pump = PumpSimulator()

# Test cavitation scenario
print("\n" + "─"*80)
print("📊 TEST: Cavitation Detection")
print("─"*80)

pump.inject_fault(FaultType.CAVITATION)
data = pump.get_sensor_reading()

result = agent.get_diagnostic(data)

print("\n🤖 AI DIAGNOSTIC:")
print("─"*80)
print(result['diagnosis'])
print("─"*80)

print(f"\n📚 References Used:")
for i, chunk in enumerate(result['context_used'], 1):
    print(f"   [{i}] Page {chunk['page']}")

print("\n" + "="*80)
print("✅ TEST COMPLETE!")
print("="*80 + "\n")
