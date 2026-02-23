// Configuración
const CONFIG = {
    features: ['FLT', 'COB', 'HLL', 'MTN', 'SPR', 'ITT', 'GC', 'OR'],
    featureNames: {
        'FLT': 'Flat',
        'COB': 'Cobbles',
        'HLL': 'Hills',
        'MTN': 'Mountain',
        'SPR': 'Sprint',
        'ITT': 'Time Trial',
        'GC': 'GC',
        'OR': 'One Day'
    },
    searchDelay: 200,
    maxSearchResults: 8
};

// Estado global
const state = {
    radarChart: null,
    currentData: null,
    allRiders: [],
    searchTimeout: null
};

// Utilidades
const $ = (id) => document.getElementById(id);
const showElement = (id, show) => $(id).style.display = show ? 'flex' : 'none';
const showError = (message) => {
    const errorDiv = $('error_message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    showElement('loading', false);
    setTimeout(() => errorDiv.style.display = 'none', 5000);
};

// API
const api = {
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = `${endpoint}${queryString ? '?' + queryString : ''}`;
        const response = await fetch(url);
        return response.json();
    }
};

// Inicialización
async function init() {
    try {
        showElement('loading', true);
        
        const ridersData = await api.get('/get_riders', { team: '' });
        
        state.allRiders = ridersData.riders;
        $('total_riders').textContent = ridersData.riders.length;
        
        showElement('loading', false);
    } catch (error) {
        showError('Error al cargar los datos iniciales');
    }
}

// Búsqueda
async function searchRiders(query) {
    clearTimeout(state.searchTimeout);
    const resultsDiv = $('search_results');
    
    if (query.length < 1) {
        resultsDiv.style.display = 'none';
        return;
    }
    
    state.searchTimeout = setTimeout(async () => {
        try {
            const data = await api.get('/search_riders', { query });
            renderSearchResults(data.riders, resultsDiv);
        } catch (error) {
            showError('Error en la búsqueda');
        }
    }, CONFIG.searchDelay);
}

function renderSearchResults(riders, container) {
    if (riders.length === 0) {
        container.innerHTML = '<div class="no-results">No se encontraron ciclistas</div>';
        container.style.display = 'block';
        return;
    }
    
    const items = riders.slice(0, CONFIG.maxSearchResults)
        .map(r => `<div class="search-result-item" onclick="selectRider('${r.replace(/'/g, "\\'")}')">${r}</div>`)
        .join('');
    
    const more = riders.length > CONFIG.maxSearchResults 
        ? `<div class="search-result-more">+${riders.length - CONFIG.maxSearchResults} más...</div>` 
        : '';
    
    container.innerHTML = items + more;
    container.style.display = 'block';
}

function selectRider(name) {
    $('search_input').value = name;
    $('search_results').style.display = 'none';
    fetchRiderDetails(name);
}

// Detalles del ciclista
async function fetchRiderDetails(name) {
    if (!name) return;
    
    try {
        showElement('loading', true);
        const data = await api.get('/get_rider_data', { name });
        state.currentData = data;
        
        $('dashboard').style.display = 'block';
        $('dashboard').classList.add('fade-in');
        
        renderRiderCard(data);
        renderStatsComparison(data.selected, data.similar[0]);
        renderSimilarTable(data.similar);
        renderChart(data.selected, data.similar[0]);
        
        showElement('loading', false);
        $('dashboard').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (error) {
        showError('Error al cargar los datos del ciclista');
    }
}

// Renderizado
function renderRiderCard(data) {
    const topSkills = getTopSpecialties(data.selected);
    
    $('rider_card').innerHTML = `
        <div class="card-header">
            <h2>${data.selected.Name}</h2>
            <div class="profile-type">${data.profile}</div>
        </div>
        <div class="card-body">
            <div class="info-grid">
                <div class="info-item">
                    <span class="label">Equipo</span>
                    <span class="value">${data.selected.Team}</span>
                </div>
                <div class="info-item">
                    <span class="label">Edad</span>
                    <span class="value">${data.selected.Age}</span>
                </div>
                <div class="info-item">
                    <span class="label">Altura</span>
                    <span class="value">${data.selected.Length}cm</span>
                </div>
                <div class="info-item">
                    <span class="label">Peso</span>
                    <span class="value">${data.selected.Weight}kg</span>
                </div>
            </div>
        </div>
        <div class="card-stats">
            <div class="stat-big">
                <span class="stat-value">${data.selected.AVG}</span>
                <span class="stat-label">Puntos AVG</span>
            </div>
            <div class="top-skills">
                ${topSkills.map(s => `<div class="skill"><span>${CONFIG.featureNames[s.name]}</span><strong>${s.value}</strong></div>`).join('')}
            </div>
        </div>
    `;
}

function renderStatsComparison(rider1, rider2) {
    const stats = CONFIG.features.map(f => `
        <div class="stat-compare">
            <div class="stat-name">${CONFIG.featureNames[f]}</div>
            <div class="stat-bars">
                <div class="bar-container">
                    <div class="bar bar-primary" style="width: ${rider1[f]}%">${rider1[f]}</div>
                </div>
                <div class="bar-container">
                    <div class="bar bar-secondary" style="width: ${rider2[f]}%">${rider2[f]}</div>
                </div>
            </div>
        </div>
    `).join('');
    
    $('stats_comparison').innerHTML = `
        <h3>Análisis Comparativo</h3>
        <div class="stats-grid">${stats}</div>
    `;
}

function renderSimilarTable(similar) {
    const rows = similar.map((r, idx) => `
        <tr>
            <td>${idx + 1}</td>
            <td><strong>${r.Name}</strong></td>
            <td><span class="profile-tag">${r.ProfileType}</span></td>
            <td>${r.Team}</td>
            <td>${r.Age}</td>
            <td>${r.AVG}</td>
            <td><span class="match-score">${(r.SimilarityScore * 100).toFixed(0)}%</span></td>
            <td class="match-text">${r.MatchReasons || '-'}</td>
            <td><button class="btn-compare" onclick="compareWith('${r.Name}')">Ver</button></td>
        </tr>
    `).join('');
    
    $('similar_body').innerHTML = rows;
}

function renderChart(main, match) {
    const ctx = $('radarChart').getContext('2d');
    if (state.radarChart) state.radarChart.destroy();
    
    state.radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: CONFIG.features.map(f => CONFIG.featureNames[f]),
            datasets: [
                createDataset(main, 'rgb(29, 53, 87)', 'rgba(29, 53, 87, 0.15)'),
                createDataset(match, 'rgb(230, 57, 70)', 'rgba(230, 57, 70, 0.15)')
            ]
        },
        options: getChartOptions()
    });
    
    renderLegend(main.Name, match.Name);
}

function createDataset(rider, borderColor, backgroundColor) {
    return {
        label: rider.Name,
        data: CONFIG.features.map(f => rider[f]),
        borderColor: borderColor,
        backgroundColor: backgroundColor,
        borderWidth: 2,
        pointBackgroundColor: borderColor,
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: borderColor,
        pointRadius: 3,
        pointHoverRadius: 5
    };
}

function getChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            r: {
                suggestMin: 50,
                suggestMax: 100,
                ticks: { stepSize: 10 },
                grid: { color: '#ddd' }
            }
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#333',
                padding: 10,
                callbacks: {
                    label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.r}`
                }
            }
        }
    };
}

function renderLegend(name1, name2) {
    $('legend').innerHTML = `
        <div class="legend-item">
            <span class="legend-color" style="background: #1d3557;"></span>
            <span>${name1}</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #e63946;"></span>
            <span>${name2}</span>
        </div>
    `;
}

// Helpers
function getTopSpecialties(rider) {
    return CONFIG.features
        .map(f => ({ name: f, value: rider[f] }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 3);
}

function compareWith(riderName) {
    fetchRiderDetails(riderName);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    init();
    
    $('search_input').oninput = (e) => searchRiders(e.target.value);
    $('search_input').onfocus = () => {
        const query = $('search_input').value;
        if (query.length >= 1) searchRiders(query);
    };
    
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-wrapper')) {
            $('search_results').style.display = 'none';
        }
    });
});
