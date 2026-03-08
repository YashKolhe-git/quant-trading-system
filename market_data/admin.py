

# Register your models here.
from django.contrib import admin
from .models import Stock, OHLCV


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "sector")
    search_fields = ("symbol", "name")


@admin.register(OHLCV)
class OHLCVAdmin(admin.ModelAdmin):
    list_display = (
        "stock",
        "trade_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
    )
    list_filter = ("stock",)
    search_fields = ("stock__symbol",)
    ordering = ("-trade_date",)
