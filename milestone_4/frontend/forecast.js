const API_MARKET_URL = "http://127.0.0.1:8000/api/market";
const API_PREDICT_URL = "http://127.0.0.1:8000/api/predict";

let chartInstance = null;

// Initialization
window.onload = () => {
    if (!localStorage.getItem('stockUser')) {
        window.location.href = 'login.html';
        return;
    }

    // Set Default Date (Tomorrow + 14 Days)
    const today = new Date();
    const futureDate = new Date(today);
    futureDate.setDate(today.getDate() + 14);
    
    const dateInput = document.getElementById('targetDate');
    if (dateInput) {
        // Min date is tomorrow
        const tomorrow = new Date(today);
        tomorrow.setDate(today.getDate() + 1);
        dateInput.min = tomorrow.toISOString().split('T')[0];
        dateInput.value = futureDate.toISOString().split('T')[0];
    }

    // Initial load
    const tickerInput = document.getElementById('forecastTicker');
    if(tickerInput && tickerInput.value) {
        fetchStockHeader(tickerInput.value);
    }
};

// Logout
const logoutBtn = document.querySelector('.logout-btn');
if(logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('stockUser');
        window.location.href = 'login.html';
    });
}

// Fetch Header Info
async function fetchStockHeader(ticker) {
    try {
        const res = await fetch(`${API_MARKET_URL}/${ticker}`);
        if (!res.ok) return null;
        const data = await res.json();
        
        setText('fullName', data.name || ticker);
        setText('tickerSymbol', data.ticker || ticker);
        setText('exchangeBadge', data.exchange || 'MARKET');
        
        if (data.data && data.data.length > 1) {
            const latest = data.data[data.data.length - 1];
            const prev = data.data[data.data.length - 2];
            const change = latest.close - prev.close;
            const pct = (change / prev.close) * 100;
            
            setText('currentPrice', latest.close.toFixed(2));
            setText('dataDate', new Date(latest.date).toLocaleDateString());
            
            const changeEl = document.getElementById('priceChange');
            if (changeEl) {
                changeEl.innerHTML = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${pct.toFixed(2)}%)`;
                changeEl.style.color = change >= 0 ? '#00C805' : '#FF5000';
            }
            return data.data; 
        }
        return null;
    } catch (e) {
        console.error("Header fetch error", e);
        return null;
    }
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
}

async function runForecast() {
    const tickerInput = document.getElementById('forecastTicker');
    const dateInput = document.getElementById('targetDate');

    if (!tickerInput || !dateInput) return;

    const ticker = tickerInput.value.trim();
    const targetDateStr = dateInput.value;
    
    // Calculate Days
    const today = new Date();
    today.setHours(0,0,0,0);
    const targetDate = new Date(targetDateStr);
    const diffTime = targetDate - today;
    const days = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 

    if (!ticker || days < 1) {
        alert("Please enter a valid ticker and a future date.");
        return;
    }

    const checkboxes = document.querySelectorAll('input[name="model"]:checked');
    const selectedModels = Array.from(checkboxes).map(cb => cb.value);

    if (selectedModels.length === 0) {
        alert("Select at least one model.");
        return;
    }

    setLoading(true);
    
    try {
        // 1. Fetch History
        const historyData = await fetchStockHeader(ticker);
        if (!historyData) throw new Error("Could not fetch historical data. check ticker.");

        // 2. Fetch Predictions individually
        const promises = selectedModels.map(async (model) => {
            try {
                const res = await fetch(`${API_PREDICT_URL}/${model}/${ticker}?days=${days}`);
                const data = await res.json();
                
                if (!res.ok) {
                    return { model, error: data.detail || "Unknown error" };
                }
                return data; // { model, forecast: [...] }
            } catch (err) {
                return { model, error: "Network Error" };
            }
        });

        const results = await Promise.all(promises);

        // 3. Separate Success and Failures
        const successResults = results.filter(r => !r.error);
        const errorResults = results.filter(r => r.error);

        // 4. Render
        if (successResults.length === 0 && errorResults.length > 0) {
            // All failed
            alert(`All models failed.\n${errorResults.map(e => `${e.model}: ${e.error}`).join('\n')}`);
        }

        renderChart(historyData, successResults);
        renderMetricCards(successResults, errorResults, historyData[historyData.length - 1].close);

    } catch (error) {
        alert(error.message);
    } finally {
        setLoading(false);
    }
}

function setLoading(isLoading) {
    const btn = document.getElementById('predictBtn');
    const resultsContainer = document.getElementById('forecastResults');
    
    if (isLoading) {
        btn.disabled = true;
        btn.querySelector('.loader').style.display = 'block';
        btn.querySelector('.btn-text').style.display = 'none';
        document.getElementById('loadingMessage').style.display = 'flex';
        if(resultsContainer) resultsContainer.innerHTML = '';
    } else {
        btn.disabled = false;
        btn.querySelector('.loader').style.display = 'none';
        btn.querySelector('.btn-text').style.display = 'block';
        document.getElementById('loadingMessage').style.display = 'none';
    }
}

function renderMetricCards(successResults, errorResults, lastClose) {
    const container = document.getElementById('forecastResults');
    if(!container) return;
    container.innerHTML = ''; 

    // Render Success Cards
    successResults.forEach(res => {
        if (!res.forecast || res.forecast.length === 0) return;

        const finalPrice = res.forecast[res.forecast.length - 1];
        const change = ((finalPrice - lastClose) / lastClose) * 100;
        const color = change >= 0 ? '#00C805' : '#FF5000';
        
        const card = document.createElement('div');
        card.className = 'metric-card';
        card.innerHTML = `
            <p class="label" style="color:${getColorForModel(res.model)}">${res.model.toUpperCase()}</p>
            <div class="metric-value-large">${finalPrice.toFixed(2)}</div>
            <p class="data" style="color: ${color}; font-weight:700;">
                ${change >= 0 ? '▲' : '▼'} ${Math.abs(change).toFixed(2)}%
            </p>
            <div style="margin-top:12px; border-top:1px solid #eee; padding-top:8px;">
                <p class="data" style="font-size:12px; color:#666;">Forecast for target date</p>
            </div>
        `;
        container.appendChild(card);
    });

    // Render Error Cards
    errorResults.forEach(err => {
        const card = document.createElement('div');
        card.className = 'metric-card';
        card.style.borderLeft = "4px solid #FF5000";
        card.innerHTML = `
            <p class="label" style="color:#666;">${err.model.toUpperCase()}</p>
            <div class="metric-value-large" style="font-size: 16px; color: #FF5000;">FAILED</div>
            <p class="data" style="font-size: 12px; margin-top:5px; color:#333;">
                ${err.error}
            </p>
        `;
        container.appendChild(card);
    });
}

function renderChart(history, results) {
    const chartEl = document.querySelector("#forecastChart");
    if (!chartEl) return;

    const contextDays = 90;
    const recentHistory = history.slice(-contextDays);
    
    // Base Series (History)
    const series = [{
        name: "Historical",
        type: 'area',
        data: recentHistory.map(item => ({ x: new Date(item.date).getTime(), y: item.close }))
    }];

    const lastDate = new Date(recentHistory[recentHistory.length - 1].date);

    // Add Forecast Series
    results.forEach(res => {
        if (!res.forecast || res.forecast.length === 0) return;

        const forecastData = [{ x: lastDate.getTime(), y: recentHistory[recentHistory.length - 1].close }];
        
        res.forecast.forEach((price, idx) => {
            const nextDate = new Date(lastDate);
            nextDate.setDate(lastDate.getDate() + (idx + 1));
            forecastData.push({ x: nextDate.getTime(), y: price });
        });

        series.push({
            name: res.model.toUpperCase(),
            type: 'line',
            data: forecastData,
            color: getColorForModel(res.model)
        });
    });

    const options = {
        series: series,
        chart: {
            height: '100%',
            type: 'line',
            toolbar: { show: false },
            fontFamily: 'inherit',
            animations: { enabled: true }
        },
        stroke: {
            width: [2, ...results.map(() => 3)],
            curve: 'smooth',
            dashArray: [0, ...results.map(() => 0)]
        },
        fill: {
            type: ['gradient', ...results.map(() => 'solid')],
            gradient: { opacityFrom: 0.4, opacityTo: 0.1 },
            opacity: [1, ...results.map(() => 1)]
        },
        xaxis: { type: 'datetime' },
        yaxis: { labels: { formatter: val => val.toFixed(0) } },
        grid: { borderColor: '#f1f1f1' },
        legend: { position: 'top' },
        colors: ['#000', ...results.map(r => getColorForModel(r.model))] 
    };

    if (chartInstance) chartInstance.destroy();
    chartInstance = new ApexCharts(chartEl, options);
    chartInstance.render();
}

function getColorForModel(modelName) {
    const colors = {
        'lstm': '#6200ea',
        'prophet': '#00bfa5',
        'xgboost': '#ff6d00',
        'arima': '#2962ff',
        'tft': '#d50000'
    };
    return colors[modelName] || '#333';
}