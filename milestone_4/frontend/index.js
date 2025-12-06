// ==========================================
// CONFIGURATION & STATE
// ==========================================
const API_BASE_URL = "http://127.0.0.1:8000/api/market";

let chartInstance = null;
let currentData = [];
let processedData = [];
let currentChartType = 'area';

// ==========================================
// INITIALIZATION
// ==========================================
window.onload = () => {
    // Authentication Check
    if (!localStorage.getItem('stockUser')) {
        window.location.href = 'login.html';
        return;
    }
    
    // Logout Handler
    document.querySelector('.logout-btn').addEventListener('click', () => {
        localStorage.removeItem('stockUser');
        window.location.href = 'login.html';
    });

    // Search Input - Enter key triggers search
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // Load Default Stock
    fetchStock("INFY.NS");
};

// ==========================================
// DATA FETCHING
// ==========================================
async function fetchStock(ticker) {
    try {
        const response = await fetch(`${API_BASE_URL}/${ticker}`);
        
        if (!response.ok) {
            throw new Error("Stock not found");
        }
        
        const result = await response.json();
        currentData = result.data;

        if (!currentData || currentData.length < 2) {
            throw new Error("Insufficient data to display");
        }
        
        // Process timestamps once for performance
        processedData = currentData.map(item => ({
            ...item,
            timestamp: new Date(item.date).getTime()
        }));
        
        updateDashboardInfo(result);
        
        // Get active period and render chart
        const activeBtn = document.querySelector('.time-selector button.active');
        const period = activeBtn ? activeBtn.innerText : '1Y';
        renderChart(period);

        // Clear search input after successful fetch
        document.getElementById('searchInput').value = '';

    } catch (error) {
        console.error("Fetch Error:", error);
        alert("Error fetching stock data. Please check the ticker symbol.");
    }
}

function handleSearch() {
    const ticker = document.getElementById('searchInput').value.trim();
    if (ticker) {
        fetchStock(ticker);
    }
}

// ==========================================
// UI UPDATE
// ==========================================
function updateDashboardInfo(apiResult) {
    const latest = currentData[currentData.length - 1];
    const prev = currentData[currentData.length - 2];
    
    const currency = apiResult.currency || 'USD';

    // Update Stock Header
    setText('fullName', apiResult.name || '--');
    setText('tickerSymbol', apiResult.ticker || '--');
    setText('exchangeBadge', apiResult.exchange || 'MARKET');
    setText('dataDate', formatDate(latest.date));
    
    // Update Current Price
    setText('currentPrice', `${currency} ${latest.close.toFixed(2)}`);

    // Update Price Change
    const change = latest.close - prev.close;
    const pct = (change / prev.close) * 100;
    const changeEl = document.getElementById('priceChange');
    changeEl.innerText = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${pct.toFixed(2)}%)`;
    changeEl.style.color = change >= 0 ? '#00C805' : '#FF5000';

    // Update Metrics
    setText('openPrice', `${currency} ${latest.open.toFixed(2)}`);
    setText('highPrice', `${currency} ${latest.high.toFixed(2)}`);
    setText('lowPrice', `${currency} ${latest.low.toFixed(2)}`);
    setText('volume', latest.volume.toLocaleString());
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) {
        el.innerText = text;
    }
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ==========================================
// CHART CONTROLS
// ==========================================
function setChartType(type) {
    currentChartType = type;
    
    // Update button states
    document.getElementById('btnLine').className = type === 'area' ? 'active' : '';
    document.getElementById('btnCandle').className = type === 'candlestick' ? 'active' : '';
    
    // Re-render chart with current period
    const activeBtn = document.querySelector('.time-selector button.active');
    renderChart(activeBtn ? activeBtn.innerText : '1Y');
}

function updateChartPeriod(period, btnElement) {
    if (btnElement) {
        // Update active state
        document.querySelectorAll('.time-selector button').forEach(btn => {
            btn.classList.remove('active');
        });
        btnElement.classList.add('active');
    }
    
    renderChart(period);
}

// ==========================================
// CHART RENDERING
// ==========================================
function renderChart(period) {
    if (!processedData.length) return;

    // Calculate data points based on period
    let days = 365;
    if (period === '1M') days = 30;
    if (period === '5Y') days = 365 * 5;

    const dataPoints = Math.min(processedData.length, Math.floor(days * 0.70));
    const slicedData = processedData.slice(-dataPoints);

    // Determine trend color
    const startPrice = slicedData[0].close;
    const endPrice = slicedData[slicedData.length - 1].close;
    const trendColor = endPrice >= startPrice ? '#00C805' : '#FF5000';

    // Prepare series data
    const seriesData = slicedData.map(item => {
        if (currentChartType === 'candlestick') {
            return {
                x: item.timestamp,
                y: [item.open, item.high, item.low, item.close]
            };
        }
        return {
            x: item.timestamp,
            y: item.close
        };
    });

    // Destroy existing chart
    if (chartInstance) {
        chartInstance.destroy();
    }

    // Chart configuration
    const options = {
        series: [{ data: seriesData }],
        chart: {
            type: currentChartType,
            height: '100%',
            width: '100%',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            parentHeightOffset: 0,
            toolbar: { show: false },
            zoom: { enabled: false },
            animations: { enabled: false }
        },
        colors: [trendColor],
        stroke: { width: currentChartType === 'area' ? 2 : 1, curve: 'straight' },
        fill: {
            type: currentChartType === 'area' ? 'gradient' : 'solid',
            gradient: { shadeIntensity: 1, opacityFrom: 0.5, opacityTo: 0.0, stops: [0, 100] }
        },
        grid: { borderColor: '#f1f1f1', padding: { top: 0, right: 40, bottom: 30, left: 10 } },
        xaxis: {
            type: 'datetime',
            tooltip: { enabled: false },
            axisBorder: { show: false },
            axisTicks: { show: false },
            labels: { hideOverlappingLabels: true, style: { colors: '#999', fontSize: '11px' }, offsetY: -5 }
        },
        yaxis: {
            opposite: true,
            tooltip: { enabled: true },
            labels: { style: { colors: '#999', fontSize: '11px' }, formatter: val => val.toFixed(0), offsetX: -10 }
        },
        dataLabels: { enabled: false },
        plotOptions: {
            candlestick: { colors: { upward: '#00C805', downward: '#FF5000' } }
        }
    };

    chartInstance = new ApexCharts(document.querySelector("#stockChart"), options);
    chartInstance.render();
}

// ==========================================
// KEYBOARD SHORTCUTS
// ==========================================
document.addEventListener('keydown', function(e) {
    // Ctrl + K to focus search input
    if (e.ctrlKey && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }
});