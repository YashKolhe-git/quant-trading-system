from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Stock, OHLCV


@require_GET
def ohlcv_view(request):
    symbol = (request.GET.get("symbol") or "").strip()
    if not symbol:
        return JsonResponse({"error": "symbol is required"}, status=400)

    stock = Stock.objects.filter(symbol=symbol).first()
    if stock is None:
        return JsonResponse({"error": "stock not found"}, status=404)

    rows = list(
        OHLCV.objects.filter(stock=stock)
        .order_by("-trade_date")
        .values("trade_date", "close_price")[:120]
    )
    rows.reverse()

    data = [
        {
            "date": row["trade_date"].isoformat(),
            "close": row["close_price"],
        }
        for row in rows
    ]
    return JsonResponse(data, safe=False)
