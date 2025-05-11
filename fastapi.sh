#bash.rc

uvicorn desafio_mosqti.server.main:app --host 0.0.0.0 --port 7000 --reload --workers 1 --timeout-keep-alive 60 --log-level info
