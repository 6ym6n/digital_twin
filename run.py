"""
Run script for Digital Twin Dashboard
Starts both FastAPI backend and React frontend
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"""
{Colors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🏭  DIGITAL TWIN - PREDICTIVE MAINTENANCE DASHBOARD  🏭   ║
║                                                              ║
║   RAG-Enhanced AI Agent for Grundfos CR Pump                ║
║   Powered by Google Gemini 2.5 & ChromaDB                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}
""")

def run_backend():
    """Run FastAPI backend server"""
    print(f"{Colors.GREEN}▶ Starting FastAPI Backend on http://localhost:8000{Colors.END}")
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    backend_path = os.path.join(backend_dir, "backend", "api.py")
    
    # Run with uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "backend.api:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], cwd=backend_dir)

def run_frontend():
    """Run React frontend dev server"""
    print(f"{Colors.BLUE}▶ Starting React Frontend on http://localhost:3000{Colors.END}")
    
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    
    # Check if node_modules exists
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print(f"{Colors.WARNING}⚠ Installing frontend dependencies...{Colors.END}")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
    
    # Run Vite dev server
    subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, shell=True)

def main():
    print_banner()
    
    mode = input(f"""
{Colors.BOLD}Choose startup mode:{Colors.END}
  [1] Backend only (FastAPI on port 8000)
  [2] Frontend only (React on port 3000)
  [3] Both (Recommended - opens browser automatically)

Enter choice (1/2/3): """).strip()

    if mode == "1":
        run_backend()
    elif mode == "2":
        run_frontend()
    elif mode == "3":
        print(f"\n{Colors.CYAN}Starting both servers...{Colors.END}")
        print(f"{Colors.WARNING}Note: Open http://localhost:3000 in your browser{Colors.END}\n")
        
        # Start backend in thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        
        # Wait a bit for backend to start
        time.sleep(3)
        
        # Open browser
        webbrowser.open("http://localhost:3000")
        
        # Run frontend (blocks)
        run_frontend()
    else:
        print(f"{Colors.FAIL}Invalid choice. Exiting.{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
