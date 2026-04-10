import subprocess
import sys
import time

# Define the correct port assignments for each service
services = [
    # (Name, Module, Port)
    ("Auth Service", "auth_service.main:app", 8000),
    ("API Gateway", "api_gateway.main:app", 8001), # New API Gateway pulled from repo
    ("Order Service", "order_service.main:app", 8002),
    ("Customer Service", "customer_service.main:app", 8003),
    ("Feedback Service", "feedback_service.main:app", 8004),
    ("Restaurant Service", "restaurant_service.main:app", 8006),
    ("Menu Service", "menu_service.main:app", 8007),
    ("Delivery Service", "delivery_service.main:app", 8008), 
]

processes = []

try:
    print("🚀 Starting all Food Ordering System microservices on their assigned ports...\n")
    for name, module, port in services:
        print(f"➜ Starting {name} on port {port}...")
        
        # We start the service using python -m uvicorn which bypasses the internal __main__
        # blocks so that hardcoded port conflicts inside the files are ignored.
        cmd = [sys.executable, "-m", "uvicorn", module, "--port", str(port)]
        
        p = subprocess.Popen(cmd)
        processes.append(p)
        time.sleep(1.5) # generous delay to stagger startups

    print("\n✅ All services started! Here are your links:")
    for name, _, port in services:
        print(f"  - {name}: http://localhost:{port}/docs")
    
    print("\n🛑 Press Ctrl+C to terminate all services.")
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\n⚠️ KeyboardInterrupt received. Shutting down all services...")
    for p in processes:
        p.terminate()
    print("Done. All services stopped.")
