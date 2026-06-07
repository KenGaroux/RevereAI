#!/bin/bash

echo "Starting DEATH.AI..."

# Clean up any existing instances
fuser -k 5000/tcp 2>/dev/null
fuser -k 8080/tcp 2>/dev/null
sleep 1

# Start Python brain in background
cd ~/deathai/python
source venv/bin/activate
python core/brain.py &
BRAIN_PID=$!
echo "Reverie brain started (PID: $BRAIN_PID)"

# Wait for brain to be ready
sleep 2

# Start Go server in background
cd ~/deathai/go
go run main.go &
GO_PID=$!
echo "Go server started (PID: $GO_PID)"

echo ""
echo "DEATH.AI is online"
echo "Browser: http://localhost:5000"
echo "Phone:   http://10.1.1.129:5000"
echo ""
echo "Press Ctrl+C to stop everything"

# Wait and catch Ctrl+C
trap "echo 'Shutting down...'; kill $BRAIN_PID $GO_PID 2>/dev/null; exit" INT
wait
