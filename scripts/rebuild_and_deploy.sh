#!/usr/bin/env bash
set -euo pipefail
# SWARMZ rebuild and deploy macro

echo "=== SWARMZ Rebuild + Deploy ==="

# 1. Clean Python artifacts
find . \( -path ./node_modules -o -path ./.git \) -prune -o -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . \( -path ./node_modules -o -path ./.git \) -prune -o -name "*.pyc" -delete 2>/dev/null || true

# 2. Lint and format
pip install ruff black -q
black . --quiet
ruff check --fix . --quiet

# 3. Backend: validate dependencies
pip install -r requirements.txt -q

# 4. Frontend: build
cd frontend
npm install --silent
npm run build
cd ..

# 5. Validate render.yaml
if command -v python3 &>/dev/null; then
  python3 -c "import yaml; yaml.safe_load(open('render.yaml'))" && echo "render.yaml: OK"
fi

# 6. Run tests
python -m pytest tests/ -q

echo "=== Build complete. Push to deploy. ==="
