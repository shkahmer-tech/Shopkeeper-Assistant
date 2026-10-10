# Smart Shopkeeper Assistant — Backend API

FastAPI backend for demand forecasting, inventory management, delivery time
prediction, and AI-generated business reviews. Refactored from a single
`ML_code.py` script into a proper `services/` + `routers/` structure.

## Folder structure

```
smart_shopkeeper_backend/
├── app/
│   ├── main.py                 # FastAPI app, registers all routers
│   ├── core/
│   │   └── config.py            # settings (CSV paths, column names, API keys)
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── services/                # business/ML logic, no FastAPI code here
│   │   ├── model_store.py       # in-memory cache of trained models
│   │   ├── demand_service.py    # train + forecast demand
│   │   ├── inventory_service.py # stock vs demand -> reorder logic
│   │   ├── delivery_service.py  # train + predict delivery time
│   │   ├── chart_service.py     # generates the analytics PNG
│   │   └── ai_review_service.py # Claude-powered business review
│   ├── routers/                 # FastAPI route definitions, call into services
│   │   ├── health.py
│   │   ├── demand.py
│   │   ├── inventory.py
│   │   ├── delivery.py
│   │   ├── charts.py
│   │   ├── ai_review.py
│   │   └── report.py            # combined end-to-end pipeline
│   └── utils/
│       └── data_loader.py       # CSV loading/cleaning shared by demand+delivery
├── data/                        # put your CSVs here (see below)
├── outputs/charts/               # generated chart PNGs land here
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd smart_shopkeeper_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env with your ANTHROPIC_API_KEY
```

Place your two datasets in `data/`:
- `retail_store_inventory.csv`
- `talabat_enhanced_orders.csv`

(Or skip this and upload a CSV directly to the `/train` endpoints instead.)

## Run

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** — this gives you an interactive Swagger
UI where you can call every route and check that each service actually
works, without needing a frontend.

## Typical flow to test everything

1. `POST /api/demand/train` — trains the demand model on your CSV
2. `POST /api/delivery/train` — trains the delivery model on your CSV
3. `POST /api/demand/forecast` — get daily/weekly/monthly demand for a date
4. `POST /api/inventory/check` — get reorder status from stock + demand numbers
5. `POST /api/delivery/predict` — get an estimated delivery time
6. `POST /api/charts/generate` — generate the analytics chart PNG
7. `POST /api/ai-review/generate` — get a plain-English AI review of the numbers
8. `POST /api/report/full` — runs steps 3–7 in one call (the "one-click" version of the old `main()`)
9. `GET /api/health` — check which models are currently trained/loaded

## Notes / known limitations (carried over from the original script)

- Categorical columns in the demand dataset are label-encoded at training
  time but not re-used at prediction time (predictions default those
  features to 0). This matches the original script's behavior — if you
  need categorical-aware single-row predictions (e.g. per-product
  forecasts), the encoders should be persisted and reused; that's a good
  next improvement.
- Trained models live in memory (`model_store.py`) and are lost on server
  restart. For production, swap this for `joblib` persistence to disk.
