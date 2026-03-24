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
  const rsiEl = document.getElementById("rsi");
  const atrEl = document.getElementById("atr");
  const volatilityEl = document.getElementById("volatility");
  const trendEl = document.getElementById("trend");
  const emaEl = document.getElementById("ema");
  const rangeEl = document.getElementById("range");

  const missingIds = [];
  if (!rsiEl) missingIds.push("rsi");
  if (!atrEl) missingIds.push("atr");
  if (!volatilityEl) missingIds.push("volatility");
  if (!trendEl) missingIds.push("trend");
  if (!emaEl) missingIds.push("ema");
  if (!rangeEl) missingIds.push("range");
  if (missingIds.length) {
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
    const setIndicator = (el, key) => {
      if (!el) return;
      const hasKey = Object.prototype.hasOwnProperty.call(data, key);
      const rawValue = hasKey ? data[key] : null;
      el.textContent = fmt(rawValue);
      console.log(`[fetchIndicators] ${key} ->`, rawValue, "rendered as", el.textContent);
    };

    // Use exact backend response keys
    setIndicator(rsiEl, "rsi_14");
    setIndicator(atrEl, "atr_14");
    setIndicator(volatilityEl, "volatility_14");
    setIndicator(trendEl, "trend_ratio");
    setIndicator(emaEl, "ema50_distance");
    setIndicator(rangeEl, "range_10");
  } catch (error) {
    console.error("[fetchIndicators] Request failed:", error);
    if (rsiEl) rsiEl.textContent = "-";
    if (atrEl) atrEl.textContent = "-";
    if (volatilityEl) volatilityEl.textContent = "-";
    if (trendEl) trendEl.textContent = "-";
    if (emaEl) emaEl.textContent = "-";
    if (rangeEl) rangeEl.textContent = "-";
  }
}

function setStockTitleFromUrl() {
  const stockTitleEl = document.getElementById("stockTitle");
  if (!stockTitleEl) return;
  const params = new URLSearchParams(window.location.search);
  const symbol = (params.get("symbol") || "").trim();
  stockTitleEl.textContent = symbol ? `Stock: ${symbol}` : "Stock: -";
  if (symbol) {
    fetchPrediction(symbol);
    fetchChartData(symbol);
    fetchIndicators(symbol);
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
