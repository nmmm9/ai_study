@echo off
chcp 65001 >nul
echo.
echo  ============================================
echo   청년정책 AI 챗봇 실행
echo  ============================================
echo.

cd /d "%~dp0"

:: ── 1. 패키지 설치 확인 ──────────────────────────────────────────
echo [1/4] 패키지 확인 중...
pip install -r requirements.txt -q
echo       완료

:: ── 2. 장학금 데이터 ChromaDB 인덱싱 ────────────────────────────
echo [2/4] 장학금 데이터 인덱싱 중...
python -c "
from dotenv import load_dotenv; load_dotenv('.env')
from backend.tools.scholarship_loader import load_all_scholarships
docs = load_all_scholarships()
print(f'       장학금 {len(docs)}개 로드 완료')
" 2>nul
echo       완료

:: ── 3. React 프론트엔드 빌드 확인 ───────────────────────────────
echo [3/4] 프론트엔드 확인 중...
if not exist "frontend\react\node_modules" (
    echo       node_modules 없음 - npm install 실행 중...
    cd frontend\react
    npm install --silent
    cd ..\..
)
echo       완료

:: ── 4. 서버 실행 ─────────────────────────────────────────────────
echo [4/4] 서버 시작...
echo.
echo  백엔드  : http://localhost:8000
echo  프론트  : http://localhost:5173  (별도 터미널에서 npm run dev)
echo  API문서 : http://localhost:8000/docs
echo.
echo  [종료하려면 Ctrl+C]
echo.

python -m uvicorn backend.server:app --reload --port 8000

pause
