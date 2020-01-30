mypy:
	poetry run mypy sucket tests

flake8:
	poetry run flake8 sucket tests

lint: mypy flake8

test:
	poetry run pytest tests
