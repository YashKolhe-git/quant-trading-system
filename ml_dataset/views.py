from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ml_dataset.services.prediction_pipeline import predict_swing


@require_GET
def predict_view(request):
    symbol = request.GET.get("symbol")
    if not symbol:
        return JsonResponse({"error": "symbol is required"}, status=400)
    try:
        result = predict_swing(symbol)
        return JsonResponse(
            {
                "symbol": result.symbol,
                "trade_date": result.trade_date.isoformat(),
                "probability": result.probability,
            }
        )
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)

