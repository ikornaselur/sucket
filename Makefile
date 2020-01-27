lint:
	poetry run mypy ./sucket
	poetry run flake8 ./sucket
