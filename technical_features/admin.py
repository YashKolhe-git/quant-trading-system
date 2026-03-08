from django.contrib import admin
from .models import TechnicalFeatureDaily


@admin.register(TechnicalFeatureDaily)
class TechnicalFeatureDailyAdmin(admin.ModelAdmin):
    list_display = (
        "stock",
        "trade_date",
        "rsi_14",
        "atr_14",
        "volatility_14",
        "volume_zscore_20",
        "volume_ratio",
        "ema20_distance",
        "ema50_distance",
        "bollinger_position",
    )

    list_filter = ("stock",)

    search_fields = ("stock__symbol",)

    ordering = ("-trade_date",)