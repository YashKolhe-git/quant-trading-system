# ML Swing Trading Analytics

An end-to-end Django + JavaScript project for swing-trading analytics:
- Ingests OHLCV market data
- Computes technical features
- Builds a supervised ML dataset
- Loads a trained Random Forest model for probability prediction
- Serves dashboard APIs consumed by a static frontend

---

## Project Structure

```text
TRADING_ANALYTICS/
├── backend/                     # Django project settings/urls
├── market_data/                 # Stock + OHLCV models, ingestion, OHLCV API
├── technical_features/          # Feature model, feature compute command, indicators API
├── ml_dataset/                  # Dataset model, prediction service, predict API
├── ml_models/                   # Trained model artifacts (.pkl)
├── frontend/                    # Static frontend (index + stock dashboard)
├── config/                      # App config (NIFTY symbols)
├── manage.py
└── requirements.txt
```

---

## Features

- **Data ingestion** from `yfinance` for configured symbols
- **Technical feature engineering** (RSI, ATR, volatility, trend/EMA/range features, etc.)
- **Dataset builder** for supervised swing labels
- **Inference pipeline**:
  - auto-check/update OHLCV
  - auto-check/update technical features
  - predict probability with trained model
- **Frontend dashboard**:
  - prediction panel
  - price chart
  - indicators panel
  - feature explanation panel
  - news panel

---

## Tech Stack

- **Backend**: Django, Django REST-style JSON endpoints, PostgreSQL
- **ML/Data**: pandas, numpy, scikit-learn, joblib
- **Market data**: yfinance
- **Frontend**: HTML, CSS, Vanilla JS, Chart.js

---

## Setup

### 1) Clone and create virtual environment

```bash
git clone <your-repo-url>
cd TRADING_ANALYTICS
python -m venv venv_trading_analytics
```

### 2) Activate environment

**Windows (PowerShell):**
```powershell
.\venv_trading_analytics\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure database

Update DB settings in:
- `backend/settings.py`

### 5) Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6) Start Django server

```bash
python manage.py runserver
```

---

## Data + ML Pipeline Commands

Run these in order:

1. **Ingest OHLCV**
```bash
python manage.py ingest_ohlcv
```

2. **Compute technical features**
```bash
python manage.py compute_technical_features
```

3. **Build swing dataset**
```bash
python manage.py build_swing_dataset
```

Model training is done offline (e.g., notebook), then save:
- `ml_models/random_forest.pkl`
- `ml_models/features.pkl`

---

## API Endpoints

### 1) Predict swing probability
`GET /api/predict?symbol=INFY.NS`

Response:
```json
{
  "symbol": "INFY.NS",
  "trade_date": "2026-03-20",
  "probability": 0.49
}
```

### 2) OHLCV for chart (last 120 points)
`GET /api/ohlcv?symbol=INFY.NS`

Response:
```json
[
  { "date": "2025-01-01", "close": 1500.0 },
  { "date": "2025-01-02", "close": 1512.0 }
]
```

### 3) Latest indicators
`GET /api/indicators?symbol=INFY.NS`

Response (example keys):
```json
{
  "rsi_14": 44.8,
  "atr_14": 34.4,
  "volatility_14": 0.018,
  "volatility_ratio": 0.79,
  "return_10": -0.03,
  "ema50_distance": -0.08,
  "trend_ratio": 0.93,
  "range_10": 84.4
}
```

### 4) News feed
`GET /api/news?symbol=INFY.NS`

Returns latest stock-related items with:
- `title`
- `source`
- `url`
- `published_at`
- `description`

---

## Frontend

Static frontend lives in `frontend/`:
- `index.html` (landing + stock search)
- `stock.html` (dashboard view)
- `style.css`
- `script.js`

Run frontend with any static server (example VS Code Live Server), then open:
- `http://127.0.0.1:5500/index.html`

Make sure Django backend is running on:
- `http://127.0.0.1:8000`

---

## Notes

- Prediction uses **TechnicalFeatureDaily** (not SwingTradingDataset).
- CORS is enabled for frontend-backend local development.
- APIs are designed for dashboard integration and explainable outputs.

---

## Future Improvements

- Add authentication and user watchlists
- Add backtesting module
- Add model/version registry
- Add LLM-based news summarization and signal explanation
- Deploy with Docker + cloud DB + CI/CD

