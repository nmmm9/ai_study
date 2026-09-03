@echo off
chcp 65001 >nul
echo.
echo  ============================================
echo   React 프론트엔드 실행
echo  ============================================
echo.

cd /d "%~dp0\frontend\react"

if not exist "node_modules" (
    echo node_modules 없음 - npm install 실행 중...
    npm install
)

echo.
echo  프론트엔드 : http://localhost:5173
echo  [종료하려면 Ctrl+C]
echo.

npm run dev

pause
