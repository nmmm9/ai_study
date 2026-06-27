@echo off
chcp 65001 > nul

start "FastAPI 백엔드" cmd /k "cd /d c:\Users\user\Desktop\ai_study\week14-final-demo\minseon && c:\Users\user\Desktop\ai_study\week14-final-demo\venv\Scripts\python.exe -m uvicorn backend.server:app --reload --port 8000"

timeout /t 2 /nobreak > nul

start "React 프론트" cmd /k "cd /d c:\Users\user\Desktop\ai_study\week14-final-demo\minseon\frontend\react && npm run dev"

echo 브라우저에서 http://localhost:5173 접속하세요
timeout /t 5
