# Update local flake inputs
update:
    nix flake update

# Sync Python dependencies and create/update venv
sync:
    uv sync

# Run the test suite
test:
    uv run pytest

# Clean previous artifacts, build sdist + wheel, and validate them
build:
    rm -rf dist/ build/ *.egg-info
    uv run python -m build
    uv run twine check dist/*

# Upload the current dist/ to TestPyPI (run `just build` first)
publish-test: build
    uv run twine upload --repository testpypi dist/*

# Upload the current dist/ to the real PyPI (run `just build` first)
publish: build
    uv run twine upload dist/*
