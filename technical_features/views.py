from django.http import JsonResponse
from django.views.decorators.http import require_GET

from market_data.models import Stock
from .models import TechnicalFeatureDaily


@require_GET
def indicators_view(request):
    symbol = (request.GET.get("symbol") or "").strip()
    if not symbol:
        return JsonResponse({"error": "symbol is required"}, status=400)

    stock = Stock.objects.filter(symbol=symbol).first()
    if stock is None:
        return JsonResponse({"error": "stock not found"}, status=404)

    row = (
        TechnicalFeatureDaily.objects.filter(stock=stock)
        .order_by("-trade_date")
        .values(
            "rsi_14",
            "atr_14",
            "volatility_14",
            "volatility_ratio",
            "return_10",
            "trend_ratio",
            "ema50_distance",
            "range_10",
        )
        .first()
    )
    if row is None:
        return JsonResponse({"error": "indicators not found"}, status=404)

    return JsonResponse(row)
