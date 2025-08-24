run:
	uvicorn main:app --reload --port 8003

lib:
	pip freeze > requirements.txt

