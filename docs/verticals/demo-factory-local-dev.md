# Demo Factory Local Dev

Demo Factory is easiest to exercise in mock mode first, then with real crawl and screenshot checks after the local renderer is running.

## Dependency Setup

From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r apps/api/requirements.txt
pip install -e packages/schemas
pip install -e packages/config
pip install -e packages/shared
pip install -e apps/api
pip install -e apps/workers

cd apps/web
npm install
npx playwright install chromium
```

## Mock Golden Path

```bash
export DEMO_FACTORY_MODEL_PROVIDER=mock
export DEMO_FACTORY_CRAWLER_PROVIDER=mock
export DEMO_FACTORY_DISABLE_SCREENSHOTS=true
export DEMO_FACTORY_RENDER_BASE_URL=http://localhost:3000
export DEMO_FACTORY_VISUAL_QA_REQUIRED=false
```

Run the targeted tests:

```bash
PYTHONPATH=apps/api:apps/workers:packages/schemas:packages/config:packages/shared \
python -m pytest apps/api/chromagora_api/tests/test_demo_factory.py -q
```

Run the smoke script:

```bash
PYTHONPATH=apps/api:apps/workers:packages/schemas:packages/config:packages/shared \
python scripts/demo_factory_smoke.py --mock
```

## Real Screenshot Mode

Start the API and web app first, then use:

```bash
unset DEMO_FACTORY_CRAWLER_PROVIDER
unset DEMO_FACTORY_DISABLE_SCREENSHOTS
export DEMO_FACTORY_MODEL_PROVIDER=mock
export DEMO_FACTORY_RENDER_BASE_URL=http://localhost:3000
export DEMO_FACTORY_VISUAL_QA_REQUIRED=true
export DEMO_FACTORY_SCREENSHOTS_REQUIRED=true
```

The renderer must be reachable at `DEMO_FACTORY_RENDER_BASE_URL` for Playwright visual QA to capture new-site screenshots.

## API Smoke

```bash
curl -X POST http://localhost:8000/demo-sites/import-csv \
  -H "Content-Type: text/csv" \
  -H "X-Filename: golden-path-3.csv" \
  --data-binary @fixtures/demo_factory/golden-path-3.csv

curl -X POST http://localhost:8000/demo-sites/batches/{batch_id}/start

PYTHONPATH=apps/api:apps/workers:packages/schemas:packages/config:packages/shared \
python -m chromagora_workers.demo_factory_worker --once --auto-start
```

## Zip Hygiene

Future exported zips should exclude local runtime state and heavyweight build/dependency folders:

```txt
.env
apps/web/.env.local
.venv
node_modules
.next
logs
__pycache__
.pytest_cache
__MACOSX
.DS_Store
```
