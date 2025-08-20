@echo off
setlocal

if not exist ".venv" (python -m venv .venv)
call .venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

if not exist ".env" (
  echo Не найден .env. Скопируй .env.example в .env и заполни при необходимости.
  pause
)

echo http://127.0.0.1:8000
uvicorn app:app --host 127.0.0.1 --port 8000 --reload

endlocal
