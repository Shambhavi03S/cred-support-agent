# Starts the FastAPI backend (Swagger UI: http://127.0.0.1:8000/docs)
$env:LLM_MODE = "MOCK_LLM"
& "$PSScriptRoot\.venv\Scripts\python.exe" -m uvicorn app.api:app --host 127.0.0.1 --port 8000
