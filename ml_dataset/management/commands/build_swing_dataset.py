from django.core.management.base import BaseCommand
from django.db import transaction

import numpy as np
import pandas as pd

from market_data.models import Stock, OHLCV
from technical_features.models import TechnicalFeatureDaily
from ml_dataset.models import SwingTradingDataset


class Command(BaseCommand):
    help = "Build supervised swing trading dataset (features + label) for ML training"

    def add_arguments(self, parser):
        parser.add_argument(
            "--stock",
            type=str,
            help="Optional: build dataset for a single stock symbol",
        )

    def handle(self, *args, **options):
        stock_symbol = options.get("stock")

        if stock_symbol:
            stocks = Stock.objects.filter(symbol=stock_symbol)
            if not stocks.exists():
                self.stdout.write(
                    self.style.ERROR(f"Stock with symbol {stock_symbol} not found.")
                )
                return
            self.stdout.write(f"Building swing dataset for {stock_symbol}")
        else:
            stocks = Stock.objects.all()
            self.stdout.write("Building swing dataset for all stocks")

        total_created = 0

        for stock in stocks.iterator():
            created_count = self._build_for_stock(stock)
            total_created += created_count
            self.stdout.write(
                self.style.SUCCESS(
                    f"{stock.symbol}: {created_count} SwingTradingDataset rows created"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Swing dataset build completed. Total new rows: {total_created}"
            )
        )

    def _build_for_stock(self, stock):
        # 1) Load OHLCV ordered by trade_date
        ohlcv_qs = (
            OHLCV.objects.filter(stock=stock)
            .order_by("trade_date")
            .values(
                "trade_date",
                "close_price",
            )
        )

        if not ohlcv_qs.exists():
            return 0

        df_price = pd.DataFrame.from_records(ohlcv_qs)
        if df_price.empty:
            return 0

        df_price = df_price.sort_values("trade_date").reset_index(drop=True)
        df_price = df_price.rename(columns={"close_price": "close"})

        # 2) Load corresponding TechnicalFeatureDaily rows
        feat_qs = (
            TechnicalFeatureDaily.objects.filter(stock=stock)
            .order_by("trade_date")
            .values(
                "trade_date",
                "rsi_14",
                "rsi_change",
                "atr_14",
                "volatility_14",
                "volatility_ratio",
                "return_5",
                "return_10",
                "ema50_distance",
                "trend_ratio",
                "range_10",
                "bollinger_position",
            )
        )

        if not feat_qs.exists():
            return 0

        df_feat = pd.DataFrame.from_records(feat_qs)
        if df_feat.empty:
            return 0

        df_feat = df_feat.sort_values("trade_date").reset_index(drop=True)

        # 3) Combine to a single DataFrame (inner join on trade_date)
        df = pd.merge(df_price, df_feat, on="trade_date", how="inner")
        df = df.sort_values("trade_date").reset_index(drop=True)

        if len(df) < 15:
            # Need at least t + 14 future closes => window length 15 (t..t+14)
            return 0

        # 4) Label computation using future window t+1..t+14 (trading-day rows)
        closes = df["close"].astype(float).to_numpy()

        # windows[i] = close[i : i+15] => entry = windows[i,0], future = windows[i,1:]
        windows = np.lib.stride_tricks.sliding_window_view(closes, window_shape=15)
        entry_price = windows[:, 0]
        future_max = windows[:, 1:].max(axis=1)
        future_min = windows[:, 1:].min(axis=1)

        max_return = (future_max - entry_price) / entry_price
        min_return = (future_min - entry_price) / entry_price

        label = ((max_return >= 0.025) & (min_return >= -0.02)).astype(int)

        # Align labeled rows to the first (n-14) dates (drops tail where window unavailable)
        df_labeled = df.iloc[: len(label)].copy()
        df_labeled["label"] = label

        # 5) Replace inf with NaN, then drop rows with any NaN features
        df_labeled = df_labeled.replace([np.inf, -np.inf], np.nan)

        feature_cols = [
            "rsi_14",
            "rsi_change",
            "atr_14",
            "volatility_14",
            "volatility_ratio",
            "return_5",
            "return_10",
            "ema50_distance",
            "trend_ratio",
            "range_10",
            "bollinger_position",
        ]

        df_labeled = df_labeled.dropna(subset=feature_cols + ["label", "trade_date"])
        if df_labeled.empty:
            return 0

        # 6) Insert rows using bulk_create(ignore_conflicts=True)
        objects_to_create = []
        for row in df_labeled.itertuples(index=False):
            objects_to_create.append(
                SwingTradingDataset(
                    stock=stock,
                    trade_date=row.trade_date,
                    rsi_14=float(row.rsi_14),
                    rsi_change=float(row.rsi_change),
                    atr_14=float(row.atr_14),
                    volatility_14=float(row.volatility_14),
                    volatility_ratio=float(row.volatility_ratio),
                    return_5=float(row.return_5),
                    return_10=float(row.return_10),
                    ema50_distance=float(row.ema50_distance),
                    trend_ratio=float(row.trend_ratio),
                    range_10=float(row.range_10),
                    bollinger_position=float(row.bollinger_position),
                    label=int(row.label),
                )
            )

        if not objects_to_create:
            return 0

        with transaction.atomic():
            created = SwingTradingDataset.objects.bulk_create(
                objects_to_create,
                ignore_conflicts=True,
            )

        return len(created)

