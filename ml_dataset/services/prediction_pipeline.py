from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from django.core.management import call_command
from django.db.models import Max

from market_data.models import Stock, OHLCV
from technical_features.models import TechnicalFeatureDaily
from ml_dataset.ml_model import model, features


@dataclass
class PredictionResult:
    symbol: str
    trade_date: date
    probability: float


def predict_swing(symbol: str) -> PredictionResult:
    """
    Orchestrate auto-update (OHLCV, features) and run predict_proba for a stock.
    """
    stock = _get_stock_or_raise(symbol)

    ensure_ohlcv_updated(symbol)
    ensure_features_updated(symbol)

    feature_row, feature_vector = get_latest_valid_features(symbol)
    X = pd.DataFrame([feature_vector], columns=features)
    probability = float(model.predict_proba(X)[0][1])

    return PredictionResult(symbol=symbol, trade_date=feature_row.trade_date, probability=probability)


def ensure_ohlcv_updated(symbol: str) -> None:
    """
    Ensure OHLCV has data up to 'today' by fetching only missing trading days.
    - Determine start_date as (latest_ohlcv_date + 1) or fallback to a fixed start.
    - Download from yfinance and insert only missing rows.
    """
    stock = _get_stock_or_raise(symbol)

    agg = OHLCV.objects.filter(stock=stock).aggregate(latest=Max("trade_date"))
    latest_ohlcv_date: Optional[date] = agg["latest"]

    if latest_ohlcv_date is None:
        start_date = date(2018, 1, 1)
    else:
        start_date = latest_ohlcv_date + timedelta(days=1)

    # Nothing to do if we're already up to date for today; yfinance will no-op anyway.
    if start_date > date.today():
        return

    df = yf.download(symbol, start=start_date.isoformat(), interval="1d", progress=False)
    if df is None or df.empty:
        return

    # Insert only missing rows; rely on (stock, trade_date) uniqueness.
    for idx, row in df.iterrows():
        trade_dt = idx.date()
        OHLCV.objects.get_or_create(
            stock=stock,
            trade_date=trade_dt,
            defaults={
                "open_price": float(row["Open"].item()),
                "high_price": float(row["High"].item()),
                "low_price": float(row["Low"].item()),
                "close_price": float(row["Close"].item()),
                "volume": int(row["Volume"].item()),
            },
        )


def ensure_features_updated(symbol: str) -> None:
    """
    Ensure TechnicalFeatureDaily is computed up to latest OHLCV date.
    Full recompute for the stock is acceptable (incremental not required).
    """
    stock = _get_stock_or_raise(symbol)

    latest_ohlcv = OHLCV.objects.filter(stock=stock).aggregate(latest=Max("trade_date"))["latest"]
    latest_feat = TechnicalFeatureDaily.objects.filter(stock=stock).aggregate(latest=Max("trade_date"))["latest"]

    if latest_ohlcv is None:
        # No OHLCV present; nothing to compute.
        return

    # If no features or features are lagging, trigger the compute command for this stock
    if latest_feat is None or latest_feat < latest_ohlcv:
        # Reuse command logic; the command will recompute for the given stock
        call_command("compute_technical_features", "--stock", symbol)


def get_latest_valid_features(symbol: str) -> Tuple[TechnicalFeatureDaily, List[float]]:
    """
    Return (row, vector) where row is the latest TechnicalFeatureDaily with all required
    features present, and vector is ordered exactly as in features.pkl.
    """
    stock = _get_stock_or_raise(symbol)

    # Build non-null filters for all required features
    qs = TechnicalFeatureDaily.objects.filter(stock=stock)
    for fname in features:
        qs = qs.exclude(**{f"{fname}__isnull": True})

    row = qs.order_by("-trade_date").first()
    if row is None:
        raise ValueError("No valid feature row with all required features present.")

    vector: List[float] = []
    for fname in features:
        value = getattr(row, fname, None)
        if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
            raise ValueError(f"Required feature '{fname}' is missing or invalid for symbol={symbol}.")
        vector.append(float(value))

    return row, vector


def _get_stock_or_raise(symbol: str) -> Stock:
    stock = Stock.objects.filter(symbol=symbol).first()
    if stock is None:
        raise ValueError(f"Stock not found: {symbol}")
    return stock

