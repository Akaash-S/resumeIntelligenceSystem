.PHONY: install start evaluate

install:
	pip install -r requirements.txt

start:
	python start.py

evaluate:
	python evaluation/evaluate.py
