# Update local flake inputs
update:
    nix flake update

# Sync Python dependencies and create/update venv
sync:
    uv sync

# Run the test suite
test:
    uv run pytest

# Build the distribution
build:
    uv run python -m build
