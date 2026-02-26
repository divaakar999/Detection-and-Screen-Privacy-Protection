#!/usr/bin/env python3
"""
Quick Start Web App Server
Simple launcher for the web application
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def main():
    print("\n" + "="*70)
    print("🌐 SHOULDER SURFING DETECTION - WEB APP")
    print("="*70)
    
    # Check if web_server.py exists
    web_server_path = Path(__file__).parent / 'web_server.py'
    
    if not web_server_path.exists():
        print("❌ Error: web_server.py not found")
        sys.exit(1)
    
    print("\n📦 Installing/updating web dependencies...")
    
    # Install Flask dependencies if needed
    try:
        import flask
        import flask_cors
        import socketio
        print("✅ Dependencies already installed\n")
    except ImportError:
        print("Installing Flask, Flask-CORS, and python-socketio...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
                             'Flask>=2.3.0', 'Flask-CORS>=4.0.0', 
                             'python-socketio>=5.9.0', 'python-engineio>=4.7.0',
                             '-q'])
        print("✅ Dependencies installed\n")
    
    print("🚀 Starting Web App Server...\n")
    print("════════════════════════════════════════════════════════════════════")
    print("📍 Web App: http://localhost:5000")
    print("📍 API: http://localhost:5000/api/")
    print("════════════════════════════════════════════════════════════════════\n")
    print("Opening browser in 2 seconds...\n")
    
    try:
        # Wait a moment for server to start
        time.sleep(2)
        
        # Open browser
        try:
            webbrowser.open('http://localhost:5000', new=2)
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("📍 Please visit http://localhost:5000 manually\n")
        
        # Start the server
        subprocess.run([sys.executable, str(web_server_path)])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
