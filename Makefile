.PHONY: run

setup:
	@echo "Installing requirements..."
	pip install -r requirements.txt
	@echo "Requirements installed!"

run:
	@echo "Running flask..."
	flask run

lint:
	@echo "Linting CoreSystemsApp..."
	ruff check
	@echo "Lint complete!"

format:
	@echo "Formatting CoreSystemsApp..."
	ruff format
	@echo "Formatting complete!"