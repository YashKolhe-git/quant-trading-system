const symbolInput = document.getElementById("symbolInput");
const predictBtn = document.getElementById("predictBtn");
const stockCards = document.querySelectorAll(".stock-card[data-symbol]");
const suggestionsEl = document.getElementById("suggestions");

const stockList = [
  "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","ITC.NS","LT.NS","AXISBANK.NS","KOTAKBANK.NS",
  "HINDUNILVR.NS","BHARTIARTL.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS","ULTRACEMCO.NS","NESTLEIND.NS","BAJFINANCE.NS",
  "HCLTECH.NS","POWERGRID.NS","TITAN.NS","NTPC.NS","TATASTEEL.NS","JSWSTEEL.NS","ONGC.NS","COALINDIA.NS","TECHM.NS",
  "WIPRO.NS","BAJAJFINSV.NS","ADANIENT.NS","ADANIPORTS.NS","DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","HEROMOTOCO.NS",
  "EICHERMOT.NS","BRITANNIA.NS","INDUSINDBK.NS","APOLLOHOSP.NS","HDFCLIFE.NS","SBILIFE.NS","UPL.NS","GRASIM.NS",
  "TATACONSUM.NS","BAJAJ-AUTO.NS","SHREECEM.NS","HINDALCO.NS","M&M.NS","BPCL.NS","IOC.NS"
];

let currentMatches = [];
let priceChart = null;

function goToStock(symbolFromCard) {
  const rawSymbol = symbolFromCard || (symbolInput ? symbolInput.value : "");
  const symbol = (rawSymbol || "").trim();
  if (!symbol) {
    return;
  }
  window.location.href = `stock.html?symbol=${encodeURIComponent(symbol)}`;
}

function hideSuggestions() {
  if (!suggestionsEl) return;
  suggestionsEl.innerHTML = "";
  suggestionsEl.classList.remove("show");
}

function positionSuggestions() {
  if (!suggestionsEl || !symbolInput) return;
  const rect = symbolInput.getBoundingClientRect();
  suggestionsEl.style.left = `${rect.left}px`;
  suggestionsEl.style.top = `${rect.bottom + 6}px`;
  suggestionsEl.style.width = `${rect.width}px`;
}

function renderSuggestions(items) {
  if (!suggestionsEl) return;
  if (!items.length) {
    hideSuggestions();
    return;
  }

  suggestionsEl.innerHTML = "";
  items.forEach((symbol) => {
    const item = document.createElement("div");
    item.className = "suggestion-item";
    item.textContent = symbol;
    item.addEventListener("click", () => {
      if (symbolInput) {
        symbolInput.value = symbol;
      }
      hideSuggestions();
      goToStock(symbol);
    });
    suggestionsEl.appendChild(item);
  });
  positionSuggestions();
  suggestionsEl.classList.add("show");
}

function updateSuggestions() {
  if (!symbolInput) return;
  const query = symbolInput.value.trim().toUpperCase();
  if (!query) {
    currentMatches = [];
    hideSuggestions();
    return;
  }
  currentMatches = stockList
    .filter((symbol) => symbol.toUpperCase().includes(query))
    .slice(0, 10);
  renderSuggestions(currentMatches);
}

if (predictBtn) {
  predictBtn.addEventListener("click", () => goToStock());
}

if (symbolInput) {
  symbolInput.addEventListener("input", updateSuggestions);
  symbolInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      if (currentMatches.length > 0) {
        goToStock(currentMatches[0]);
      } else {
        goToStock();
      }
    }
  });
  symbolInput.addEventListener("focus", updateSuggestions);
}

window.addEventListener("resize", () => {
  if (suggestionsEl && suggestionsEl.classList.contains("show")) {
    positionSuggestions();
  }
});

window.addEventListener("scroll", () => {
  if (suggestionsEl && suggestionsEl.classList.contains("show")) {
    positionSuggestions();
  }
}, true);

stockCards.forEach((card) => {
  card.addEventListener("click", () => {
    const symbol = card.getAttribute("data-symbol");
    goToStock(symbol);
  });
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      const symbol = card.getAttribute("data-symbol");
      goToStock(symbol);
    }
  });
  if (!card.hasAttribute("tabindex")) {
    card.setAttribute("tabindex", "0");
  }
  card.setAttribute("role", "button");
});

document.addEventListener("click", (event) => {
  const clickedSuggestions = suggestionsEl && suggestionsEl.contains(event.target);
  const clickedInput = symbolInput && symbolInput.contains(event.target);
  if (!clickedSuggestions && !clickedInput) {
    hideSuggestions();
  }
});

async function fetchPrediction(symbol) {
  const symbolEl = document.getElementById("symbol");
  const dateEl = document.getElementById("date");
  const probabilityEl = document.getElementById("probability");
  const signalEl = document.getElementById("signal");

  if (!symbolEl || !dateEl || !probabilityEl || !signalEl) {
    return;
  }

  try {
    const url = `http://127.0.0.1:8000/api/predict?symbol=${encodeURIComponent(symbol)}`;
    console.log("[fetchPrediction] Calling URL:", url);
    const response = await fetch(url);
    const data = await response.json();
    console.log("[fetchPrediction] Response JSON:", data);

    if (!response.ok || data.error) {
      throw new Error(data.error || "Failed to fetch prediction");
    }

    const probability = Number(data.probability);
    let signal = "Weak";
    if (probability >= 0.6) {
      signal = "Strong";
    } else if (probability >= 0.5) {
      signal = "Medium";
    }

    symbolEl.textContent = data.symbol ?? symbol;
    dateEl.textContent = data.trade_date ?? "-";
    probabilityEl.textContent = Number.isFinite(probability) ? probability.toFixed(2) : "-";
    signalEl.textContent = signal;
  } catch (error) {
    console.error("[fetchPrediction] Request failed:", error);
    console.warn("[fetchPrediction] If this is blocked in browser console, enable CORS on backend for http://127.0.0.1:5500.");
    symbolEl.textContent = symbol;
    dateEl.textContent = "-";
    probabilityEl.textContent = "-";
    signalEl.textContent = "Weak";
  }
}

async function fetchChartData(symbol) {
  const chartContainer = document.getElementById("chart");
  const canvas = document.getElementById("priceChartCanvas");
  if (!chartContainer || !canvas || typeof Chart === "undefined") {
    return;
  }

  try {
    const url = `http://127.0.0.1:8000/api/ohlcv?symbol=${encodeURIComponent(symbol)}`;
    console.log("[fetchChartData] Calling URL:", url);
    const response = await fetch(url);
    const data = await response.json();
    console.log("[fetchChartData] Response JSON:", data);
    if (!response.ok || !Array.isArray(data)) {
      throw new Error("Failed to fetch chart data");
    }

    const validRows = [];
    for (const row of data) {
      if (!row || row.date == null || row.close == null) {
        continue;
      }

      const dateValue = String(row.date).trim();
      const closeValue = Number(row.close);

      if (!dateValue || Number.isNaN(Date.parse(dateValue))) {
        continue;
      }
      if (!Number.isFinite(closeValue)) {
        continue;
      }

      validRows.push({ date: dateValue, close: closeValue });
    }

    console.log(`[fetchChartData] Using ${validRows.length} valid points for ${symbol}`);
    if (validRows.length === 0) {
      throw new Error("No valid OHLCV rows available for chart");
    }

    const dates = validRows.map((row) => row.date);
    const closes = validRows.map((row) => row.close);

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    if (priceChart) {
      priceChart.destroy();
    }

    priceChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: dates,
        datasets: [
          {
            label: `${symbol} Close`,
            data: closes,
            borderColor: "#7dd3fc",
            backgroundColor: "rgba(125, 211, 252, 0.14)",
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.25,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: "#dbe8ff",
            },
          },
        },
        scales: {
          x: {
            ticks: { color: "#9fb0d9", maxTicksLimit: 10 },
            grid: { color: "rgba(159, 176, 217, 0.15)" },
          },
          y: {
            ticks: { color: "#9fb0d9" },
            grid: { color: "rgba(159, 176, 217, 0.15)" },
          },
        },
      },
    });
  } catch (error) {
    console.error("[fetchChartData] Request failed:", error);
    if (priceChart) {
      priceChart.destroy();
      priceChart = null;
    }
    chartContainer.setAttribute("data-chart-error", "Unable to load chart data.");
  }
}

async function fetchIndicators(symbol) {
  const indicatorMap = {
    rsi_14: "rsi",
    atr_14: "atr",
    volatility_14: "volatility",
    volatility_ratio: "volatilityRatio",
    return_10: "return10",
    ema50_distance: "ema",
    trend_ratio: "trend",
    range_10: "range",
  };
  const indicatorElements = {};
  const missingIds = [];
  Object.values(indicatorMap).forEach((id) => {
    const el = document.getElementById(id);
    indicatorElements[id] = el;
    if (!el) {
      missingIds.push(id);
    }
  });
  if (missingIds.length > 0) {
    console.warn("[fetchIndicators] Missing indicator elements:", missingIds);
  }

  try {
    const url = `http://127.0.0.1:8000/api/indicators?symbol=${encodeURIComponent(symbol)}`;
    console.log("[fetchIndicators] Calling URL:", url);
    const response = await fetch(url);
    const data = await response.json();
    console.log("[fetchIndicators] Response JSON:", data);

    if (!response.ok || data.error || typeof data !== "object" || data === null) {
      throw new Error(data.error || "Failed to fetch indicators");
    }
    console.log("[fetchIndicators] Available keys:", Object.keys(data));

    const fmt = (value) => (Number.isFinite(Number(value)) ? Number(value).toFixed(4) : "-");
    Object.entries(indicatorMap).forEach(([apiKey, spanId]) => {
      const el = indicatorElements[spanId];
      if (!el) return;
      const hasKey = Object.prototype.hasOwnProperty.call(data, apiKey);
      const rawValue = hasKey ? data[apiKey] : null;
      el.textContent = fmt(rawValue);
      console.log(`[fetchIndicators] ${apiKey} ->`, rawValue, "rendered as", el.textContent);
    });

    generateFeatureExplanation(data);
  } catch (error) {
    console.error("[fetchIndicators] Request failed:", error);
    Object.values(indicatorElements).forEach((el) => {
      if (el) el.textContent = "-";
    });
    generateFeatureExplanation(null);
  }
}

function generateFeatureExplanation(indicators) {
  const featuresEl = document.getElementById("features");
  if (!featuresEl) return;

  if (!indicators || typeof indicators !== "object") {
    featuresEl.innerHTML = `<div class="muted">Feature explanation unavailable.</div>`;
    return;
  }

  const rsi = Number(indicators.rsi_14);
  const trendRatio = Number(indicators.trend_ratio);
  const emaDistance = Number(indicators.ema50_distance);
  const volatility = Number(indicators.volatility_14);
  const recentReturn = Number(indicators.return_10);
  const range10 = Number(indicators.range_10);

  const points = [];
  const v = (x) => Number(x).toFixed(4);

  // RSI explanation
  if (Number.isFinite(rsi)) {
    if (rsi < 30) {
      points.push(
        `RSI is low (${v(rsi)}), indicating the stock is in an oversold region, which may suggest a potential rebound.`
      );
    } else if (rsi < 40) {
      points.push(
        `RSI is slightly low (${v(rsi)}), suggesting mild oversold conditions and a possible upward correction.`
      );
    } else if (rsi <= 60) {
      points.push(
        `RSI is neutral (${v(rsi)}), indicating balanced momentum without strong directional bias.`
      );
    } else if (rsi <= 70) {
      points.push(
        `RSI is slightly high (${v(rsi)}), suggesting mild overbought conditions.`
      );
    } else {
      points.push(
        `RSI is high (${v(rsi)}), indicating overbought conditions and a potential pullback.`
      );
    }
  }

  // Trend ratio explanation
  if (Number.isFinite(trendRatio)) {
    if (trendRatio < 0.95) {
      points.push(
        `Trend ratio is low (${v(trendRatio)}), indicating weak momentum and a lack of strong directional movement.`
      );
    } else if (trendRatio <= 1.05) {
      points.push(
        `Trend ratio is near neutral (${v(trendRatio)}), suggesting sideways movement with no clear trend.`
      );
    } else {
      points.push(
        `Trend ratio is high (${v(trendRatio)}), indicating strong upward momentum.`
      );
    }
  }

  // EMA50 distance explanation
  if (Number.isFinite(emaDistance)) {
    if (emaDistance < 0) {
      points.push(
        `Price is below EMA50 (${v(emaDistance)}), suggesting bearish positioning relative to recent average price.`
      );
    } else if (emaDistance > 0) {
      points.push(
        `Price is above EMA50 (${v(emaDistance)}), indicating bullish positioning.`
      );
    }
  }

  // Volatility explanation
  if (Number.isFinite(volatility)) {
    if (volatility > 0.02) {
      points.push(
        `Volatility is relatively high (${v(volatility)}), indicating larger price swings and higher risk.`
      );
    } else {
      points.push(
        `Volatility is low (${v(volatility)}), suggesting stable price movement.`
      );
    }
  }

  // Return explanation
  if (Number.isFinite(recentReturn)) {
    if (recentReturn < 0) {
      points.push(
        `Recent returns are negative (${v(recentReturn)}), indicating short-term weakness in price.`
      );
    } else if (recentReturn > 0) {
      points.push(
        `Recent returns are positive (${v(recentReturn)}), indicating short-term strength.`
      );
    }
  }

  // Range explanation
  if (Number.isFinite(range10)) {
    // Practical threshold for current universe: larger than 100 indicates wider swings.
    if (range10 > 100) {
      points.push(
        `Price range is wide (${v(range10)}), indicating strong price movement over recent sessions.`
      );
    } else {
      points.push(
        `Price range is narrow (${v(range10)}), suggesting limited price movement.`
      );
    }
  }

  if (!points.length) {
    featuresEl.innerHTML = `<div class="muted">Not enough indicator data for explanation.</div>`;
    return;
  }

  featuresEl.innerHTML = `<ul class="feature-points">${points
    .map((point) => `<li>${point}</li>`)
    .join("")}</ul>`;
}

async function fetchNews(symbol) {
  const newsEl = document.getElementById("news");
  if (!newsEl) return;

  try {
    const url = `http://127.0.0.1:8000/api/news?symbol=${encodeURIComponent(symbol)}`;
    console.log("[fetchNews] Calling URL:", url);
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok || !Array.isArray(data)) {
      throw new Error("Failed to fetch news");
    }

    if (!data.length) {
      newsEl.innerHTML = `<div class="muted">No news found.</div>`;
      return;
    }

    newsEl.innerHTML = "";
    data.forEach((item) => {
      const title = item.title ?? "";
      const source = item.source ?? "";
      const publishedAt = item.published_at ?? "";
      const itemUrl = item.url ?? "";

      const wrapper = document.createElement("div");
      wrapper.className = "news-item";
      wrapper.innerHTML = `
        <div class="news-title">
          <a href="${itemUrl}" target="_blank" rel="noopener noreferrer">${title}</a>
        </div>
        <div class="news-meta">${source}${publishedAt ? " • " + publishedAt : ""}</div>
      `;

      newsEl.appendChild(wrapper);
    });
  } catch (error) {
    console.error("[fetchNews] Request failed:", error);
    newsEl.innerHTML = `<div class="muted">Unable to load news.</div>`;
  }
}

function setStockTitleFromUrl() {
  const stockTitleEl = document.getElementById("stockTitle");
  if (!stockTitleEl) return;
  const params = new URLSearchParams(window.location.search);
  const symbol = (params.get("symbol") || "").trim();
  console.log("[setStockTitleFromUrl] symbol:", symbol);
  stockTitleEl.textContent = symbol ? `Stock: ${symbol}` : "Stock: -";
  if (symbol) {
    fetchPrediction(symbol);
    fetchChartData(symbol);
    Promise.resolve().then(() => fetchIndicators(symbol));
    Promise.resolve().then(() => fetchNews(symbol));
  }
}

function initPage() {
  setStockTitleFromUrl();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initPage);
} else {
  initPage();
}
