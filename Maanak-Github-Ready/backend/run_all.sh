#!/bin/bash

# Ensure we are in MY_WORK directory
cd "$(dirname "$0")"

echo "==================================="
echo "  MAANAK INTEGRATION TEST SCRIPT   "
echo "==================================="

# 1. Install frontend dependencies
echo "-> Installing Frontend dependencies..."
cd ../frontend
# Provide the FastAPI url in .env.local
echo "NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000" > .env.local
npm install

# Start Frontend in background
echo "-> Starting Next.js Frontend (Port 3000)..."
npm run dev > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../../

# 2. Start the Microservices
echo "-> Starting Collective Memory (Port 8002)..."
cd Collective_Memory
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8002 > ../collective.log 2>&1 &
COLLECTIVE_PID=$!
cd ..

echo "-> Starting RaG_GuY (Port 8001)..."
cd RaG_GuY
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 > ../rag.log 2>&1 &
RAG_PID=$!
cd ..

# 3. Start the Python Gateway
echo "-> Starting Python Gateway (Port 8000)..."
cd Input_Processing
source ../../venv/bin/activate
python api.py > ../gateway.log 2>&1 &
GATEWAY_PID=$!
cd ..

echo "==================================="
echo " ALL SERVERS RUNNING! "
echo " Frontend:          http://localhost:3000 "
echo " Gateway:           http://localhost:8000 "
echo " RaG_GuY:           http://localhost:8001 "
echo " Collective_Memory: http://localhost:8002 "
echo "==================================="
echo "Press CTRL+C to stop all servers."

# Trap CTRL+C to kill both background processes
trap "echo 'Stopping servers...'; kill $FRONTEND_PID $GATEWAY_PID $RAG_PID $COLLECTIVE_PID; exit" INT

# Wait to keep the script running
wait
