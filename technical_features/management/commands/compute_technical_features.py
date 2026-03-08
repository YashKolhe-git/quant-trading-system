from django.core.management.base import BaseCommand
from django.db import transaction

import pandas as pd
import numpy as np

from market_data.models import Stock, OHLCV
from technical_features.models import TechnicalFeatureDaily


class Command(BaseCommand):
    help = "Compute technical features for OHLCV data and store in TechnicalFeatureDaily"

    def add_arguments(self, parser):
        parser.add_argument(
            "--stock",
            type=str,
            help="Optional: compute technical features for a single stock symbol",
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
            self.stdout.write(f"Computing technical features for {stock_symbol}")
        else:
            stocks = Stock.objects.all()
            self.stdout.write("Computing technical features for all stocks")

        total_created = 0

        for stock in stocks.iterator():
            created_count = self._compute_for_stock(stock)
            total_created += created_count
            self.stdout.write(
                self.style.SUCCESS(
                    f"{stock.symbol}: {created_count} TechnicalFeatureDaily rows created"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Technical feature computation completed. Total new rows: {total_created}"
            )
        )

    def _compute_for_stock(self, stock):
        """
        Compute all requested technical indicators for a single stock and
        bulk insert into TechnicalFeatureDaily, avoiding duplicates.
        """
        # Fetch OHLCV data for this stock
        qs = (
            OHLCV.objects.filter(stock=stock)
            .order_by("trade_date")
            .values(
                "trade_date",
                "open_price",
                "high_price",
                "low_price",
                "close_price",
                "volume",
            )
        )

        if not qs.exists():
            return 0

        df = pd.DataFrame.from_records(qs)
        if df.empty:
            return 0

        # Sort explicitly by trade_date to be safe
        df = df.sort_values("trade_date").reset_index(drop=True)

        # Rename to simpler column names for calculations
        df = df.rename(
            columns={
                "open_price": "open",
                "high_price": "high",
                "low_price": "low",
                "close_price": "close",
                "volume": "volume",
            }
        )

        # 1) Price change (delta)
        delta = df["close"].diff()

        # 2) Gain / Loss
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # 3) RSI (14)
        window_rsi = 14
        avg_gain = gain.rolling(window_rsi).mean()
        avg_loss = loss.rolling(window_rsi).mean()

        rs = avg_gain / avg_loss
        rsi_14 = 100 - (100 / (1 + rs))

        # 4) True Range (TR)
        tr1 = df["high"] - df["low"]
        prev_close = df["close"].shift()

        tr2 = (df["high"] - prev_close).abs()
        tr3 = (df["low"] - prev_close).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 5) ATR (14)
        window_atr = 14
        atr_14 = tr.rolling(window_atr).mean()

        # 6) Daily returns
        returns = df["close"].pct_change()

        # 7) Rolling volatility (14)
        window_vol = 14
        volatility_14 = returns.rolling(window_vol).std()

        # 8) Volume Z-score (20)
        window_vol_z = 20
        volume_mean = df["volume"].rolling(window_vol_z).mean()
        volume_std = df["volume"].rolling(window_vol_z).std()
        volume_zscore_20 = (df["volume"] - volume_mean) / volume_std

        # 9) Volume Ratio
        volume_sma_20 = df["volume"].rolling(20).mean()
        volume_ratio = df["volume"] / volume_sma_20

        # 10) EMA Trend Distances
        ema20 = df["close"].ewm(span=20, adjust=False).mean()
        ema50 = df["close"].ewm(span=50, adjust=False).mean()
        ema20_distance = (df["close"] - ema20) / df["close"]
        ema50_distance = (df["close"] - ema50) / df["close"]

        # 11) Bollinger Position
        bb_middle = df["close"].rolling(20).mean()
        bb_std = df["close"].rolling(20).std()
        bb_upper = bb_middle + (2 * bb_std)
        bb_lower = bb_middle - (2 * bb_std)
        bollinger_position = (df["close"] - bb_lower) / (bb_upper - bb_lower)

        # Assemble final DataFrame
        features_df = pd.DataFrame(
            {
                "trade_date": df["trade_date"],
                "rsi_14": rsi_14,
                "atr_14": atr_14,
                "volatility_14": volatility_14,
                "volume_zscore_20": volume_zscore_20,
                "volume_ratio": volume_ratio,
                "ema20_distance": ema20_distance,
                "ema50_distance": ema50_distance,
                "bollinger_position": bollinger_position,
            }
        )

        # Clean up infinities / NaNs
        features_df = features_df.replace([np.inf, -np.inf], np.nan)

        objects_to_create = []

        for row in features_df.itertuples(index=False):
            trade_date = row.trade_date

            obj = TechnicalFeatureDaily(
                stock=stock,
                trade_date=trade_date,
                rsi_14=_to_float_or_none(row.rsi_14),
                atr_14=_to_float_or_none(row.atr_14),
                volatility_14=_to_float_or_none(row.volatility_14),
                volume_zscore_20=_to_float_or_none(row.volume_zscore_20),
                volume_ratio=_to_float_or_none(row.volume_ratio),
                ema20_distance=_to_float_or_none(row.ema20_distance),
                ema50_distance=_to_float_or_none(row.ema50_distance),
                bollinger_position=_to_float_or_none(row.bollinger_position),
            )
            objects_to_create.append(obj)

        if not objects_to_create:
            return 0

        with transaction.atomic():
            created = TechnicalFeatureDaily.objects.bulk_create(
                objects_to_create,
                ignore_conflicts=True,
            )

        return len(created)


def _to_float_or_none(value):
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int_or_none(value):
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
    except TypeError:
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

