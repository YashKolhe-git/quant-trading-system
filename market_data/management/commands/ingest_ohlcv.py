from django.core.management.base import BaseCommand
from market_data.models import Stock, OHLCV
from config.settings import NIFTY_50_SYMBOLS

import yfinance as yf


class Command(BaseCommand):
    help = "Ingest daily OHLCV data for NIFTY 50 stocks"

    def handle(self, *args, **options):
        start_date = "2018-01-01"

        for symbol in NIFTY_50_SYMBOLS:
            self.stdout.write(f"Fetching data for {symbol}")

            # Ensure stock exists
            stock, _ = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={"name": symbol.replace(".NS", "")}
            )

            # Download OHLCV data
            df = yf.download(
                symbol,
                start=start_date,
                interval="1d",
                progress=False
            )

            if df.empty:
                self.stdout.write(
                    self.style.WARNING(f"No data found for {symbol}")
                )
                continue

            records_created = 0

            # Iterate day by day
            for _, row in df.iterrows():
                trade_date = row.name.date()

                _, created = OHLCV.objects.get_or_create(
                    stock=stock,
                    trade_date=trade_date,
                    defaults={
                        "open_price": float(row["Open"].iloc[0]),
                        "high_price": float(row["High"].iloc[0]),
                        "low_price": float(row["Low"].iloc[0]),
                        "close_price": float(row["Close"].iloc[0]),
                        "volume": int(row["Volume"].iloc[0]),
                    }
                )

                if created:
                    records_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{symbol}: {records_created} new records inserted"
                )
            )

        self.stdout.write(
            self.style.SUCCESS("OHLCV ingestion completed successfully")
        )
