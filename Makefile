mypy:
	poetry run mypy sucket tests

flake8:
	poetry run flake8 sucket tests

black:
	poetry run black sucket tests --check

isort:
	poetry run isort -c -rc sucket tests

lint: mypy flake8 black

test:
	poetry run pytest tests
