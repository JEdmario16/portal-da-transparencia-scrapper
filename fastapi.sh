#bash.rc

uvicorn desafio_mosqti.server.main:app --host 0.0.0.0 --port 5000 --reload --workers 5
