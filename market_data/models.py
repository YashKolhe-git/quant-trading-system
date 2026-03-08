from django.db import models

#create your models here.
from django.db import models


class Stock(models.Model):
    """
    Represents the 'stocks' table
    """
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.symbol


class OHLCV(models.Model):
    """
    Represents the 'ohlcv_daily' table
    """
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name="ohlcv"
    )
    trade_date = models.DateField()

    open_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    close_price = models.FloatField()
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ("stock", "trade_date")
        indexes = [
            models.Index(fields=["stock", "trade_date"]),
        ]
        ordering = ["trade_date"]

    def __str__(self):
        return f"{self.stock.symbol} | {self.trade_date}"
