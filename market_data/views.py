from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Stock, OHLCV

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import timedelta
from django.utils import timezone
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen


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


@require_GET
def news_view(request):
    symbol = (request.GET.get("symbol") or "").strip()
    if not symbol:
        return JsonResponse({"error": "symbol is required"}, status=400)

    # Example: TCS.NS -> TCS, INFY.NS -> INFY
    stock_name = symbol.split(".", 1)[0]

    # RSS source (no API key required): Google News search feed
    query = f"{stock_name} stock"
    rss_url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(query)
        + "&hl=en-IN&gl=IN&ceid=IN:en"
    )

    req = Request(
        rss_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; trading-analytics/1.0; +https://example.com)"
        },
    )

    try:
        with urlopen(req, timeout=15) as resp:
            raw_xml = resp.read()
    except Exception as exc:
        return JsonResponse({"error": f"Failed to fetch news: {exc}"}, status=502)

    try:
        root = ET.fromstring(raw_xml)
    except Exception:
        return JsonResponse({"error": "Failed to parse news feed"}, status=502)

    items = root.findall(".//item")

    cutoff_7d = timezone.now() - timedelta(days=7)
    cutoff_30d = timezone.now() - timedelta(days=30)

    recent_7d = []
    recent_30d = []
    any_items = []

    # Google News RSS is typically already sorted newest-first. We keep that order.
    for item in items[:40]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()

        published_dt = None
        published_at = None
        try:
            published_dt = parsedate_to_datetime(pub_date_raw)
            if published_dt is not None:
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
                published_dt = published_dt.astimezone(timezone.utc)
                published_at = published_dt.isoformat()
        except Exception:
            published_dt = None
            published_at = pub_date_raw or None

        source = urlparse(link).netloc if link else None

        payload = {
            "title": title,
            "source": source,
            "url": link,
            "published_at": published_at,
            "description": description,
        }

        any_items.append(payload)

        if published_dt is not None:
            if published_dt >= cutoff_30d:
                recent_30d.append(payload)
            if published_dt >= cutoff_7d:
                recent_7d.append(payload)

    # Fallback logic:
    # 1) last 7 days
    # 2) last 30 days
    # 3) latest available without filtering
    selected = recent_7d or recent_30d or any_items
    return JsonResponse(selected[:8], safe=False)
