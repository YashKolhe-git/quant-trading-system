from django.db import models

# Create your models here.
from django.db import models
from market_data.models import Stock


class TechnicalFeatureDaily(models.Model):
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name="technical_features"
    )

    trade_date = models.DateField()

    # Momentum
    rsi_14 = models.FloatField(null=True, blank=True)
    rsi_change = models.FloatField(null=True, blank=True)

    # Volatility / Risk
    atr_14 = models.FloatField(null=True, blank=True)
    volatility_14 = models.FloatField(null=True, blank=True)
    volatility_ratio = models.FloatField(null=True, blank=True)

    # Returns
    return_5 = models.FloatField(null=True, blank=True)
    return_10 = models.FloatField(null=True, blank=True)

    # Trend
    ema50_distance = models.FloatField(null=True, blank=True)
    trend_ratio = models.FloatField(null=True, blank=True)

    # Price Range
    range_10 = models.FloatField(null=True, blank=True)

    # Bollinger Bands
    bollinger_position = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("stock", "trade_date")
        indexes = [
            models.Index(fields=["stock", "trade_date"]),
            models.Index(fields=["trade_date"]),
        ]

    def __str__(self):
        return f"{self.stock.symbol} - {self.trade_date}"
