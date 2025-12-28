.PHONY: run setup lint lint-all lint-html lint-css format

setup:
	@echo "Installing Python requirements..."
	pip install -r requirements.txt
	@echo "Installing Node.js dependencies..."
	npm install
	@echo "Requirements installed!"

run:
	@echo "Running flask..."
	flask run

lint:
	@echo "Linting Python files..."
	ruff check
	@echo "Python lint complete!"

lint-html:
	@echo "Linting HTML templates..."
	npx htmlhint 'app/templates/**/*.html'
	@echo "HTML lint complete!"

lint-css:
	@echo "Linting CSS files..."
	npx stylelint 'app/static/styles/**/*.css'
	@echo "CSS lint complete!"

format:
	@echo "Formatting Python code..."
	ruff format
	@echo "Python formatting complete!"
