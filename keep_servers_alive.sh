#!/bin/bash
# Keep servers alive by checking every 30 seconds and restarting if needed

cd /c/Users/Rkavavu/OneDrive/Desktop/MEDIASSIST-AI

while true; do
    # Check backend
    backend_running=$(netstat -ano | grep ':5000 ' | grep LISTENING | wc -l)
    if [ "$backend_running" -eq 0 ]; then
        echo "$(date): Backend down, restarting..."
        cd backend && source ../venv/Scripts/activate && nohup python run.py > backend_server.log 2>&1 &
        cd ..
    fi
    
    # Check frontend
    frontend_running=$(netstat -ano | grep ':5173 ' | grep LISTENING | wc -l)
    if [ "$frontend_running" -eq 0 ]; then
        echo "$(date): Frontend down, restarting..."
        cd frontend && nohup npm run dev > frontend_server.log 2>&1 &
        cd ..
    fi
    
    sleep 30
done
