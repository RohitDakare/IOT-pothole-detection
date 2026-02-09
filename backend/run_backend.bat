@echo off
echo Installing backend dependencies...
pip install -r requirements.txt
echo Starting FastAPI Backend...
echo The dashboard will be available at http://localhost:8000
python main.py
pause
