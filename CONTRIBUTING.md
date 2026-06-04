# Contributing to CoreSystemsApp

Thanks for your interest in improving CoreSystemsApp, the LSUHSC-CAIPP Bioinformatics and Modeling Cores management system.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
npm install
```

The app uses SQLite by default for user credentials and connects to MySQL databases for Core B and Core C data. Copy the example configs in `db_config_example/` into a `db_config/` directory and fill in your own credentials before running.

To run the app:

```bash
flask run
```

## Contribution Scope

Useful contributions include:

- new or improved routes and blueprints under `app/CoreB/` and `app/CoreC/`,
- improvements to the shared table abstraction (`app/abstract_classes/`, `app/interfaces/`),
- fuzzy search and filtering improvements in `app/utils/search_utils.py`,
- dashboard and reporting enhancements in `app/CoreB/graphs/`,
- bug fixes in invoice PDF generation (`app/pdfwriter/`),
- test coverage for reusable Python modules,
- HTML template and CSS cleanup/improvement in `app/templates/` and `app/static/`.

## Coding Guidelines

- Keep functions small and focused.
- Add or maintain docstrings for non-trivial behavior.
- Follow the existing table abstraction (interface to abstract class to concrete class) when adding new database-backed features.
- Use parameterized queries through `db_utils` rather than string-formatting SQL.
- Register new blueprints in `app/__init__.py` (see `app/README.md`).

## Linting and Formatting

The project uses Ruff (Python), HTMLHint (templates), and Stylelint (CSS). Run them through the Makefile:

```bash
make lint        # Ruff (Python)
make lint-html   # HTMLHint (templates)
make lint-css    # Stylelint (CSS)
make format      # Ruff formatter
```

## Testing

Run the test suite before submitting:

```bash
python -m pytest
```

Tests live under `tests/`. Please add coverage for new utility functions and any non-trivial logic.

## Pull Requests

Please include:

1. What changed and why.
2. Reproduction or validation steps.
3. Any database schema impact (note new tables or columns).
4. Screenshots for visible UI changes.

## Data and Privacy

- Do not commit database credentials. The `db_config/` directory should stay out of version control.
- Do not commit proprietary or personally identifying data (PI records, invoices, uploaded files).
- Keep example configs in `db_config_example/` free of real credentials.
