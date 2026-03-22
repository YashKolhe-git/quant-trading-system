from django.contrib import admin

from .models import SwingTradingDataset


@admin.register(SwingTradingDataset)
class SwingTradingDatasetAdmin(admin.ModelAdmin):
    list_display = (
        "stock",
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
        "label",
    )
    list_filter = ("stock", "label")
    search_fields = ("stock__symbol",)
    ordering = ("-trade_date",)

