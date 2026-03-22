from django.db import models

from market_data.models import Stock


class SwingTradingDataset(models.Model):
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name="swing_trading_dataset",
    )
    trade_date = models.DateField()

    # Features copied from TechnicalFeatureDaily
    rsi_14 = models.FloatField(null=True, blank=True)
    rsi_change = models.FloatField(null=True, blank=True)
    atr_14 = models.FloatField(null=True, blank=True)
    volatility_14 = models.FloatField(null=True, blank=True)
    volatility_ratio = models.FloatField(null=True, blank=True)
    return_5 = models.FloatField(null=True, blank=True)
    return_10 = models.FloatField(null=True, blank=True)
    ema50_distance = models.FloatField(null=True, blank=True)
    trend_ratio = models.FloatField(null=True, blank=True)
    range_10 = models.FloatField(null=True, blank=True)
    bollinger_position = models.FloatField(null=True, blank=True)

    # Label: 1 = swing opportunity, 0 = no opportunity
    label = models.IntegerField()

    class Meta:
        unique_together = ("stock", "trade_date")
        indexes = [
            models.Index(fields=["stock", "trade_date"]),
        ]

    def __str__(self):
        return f"{self.stock.symbol} - {self.trade_date} - {self.label}"

