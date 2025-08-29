// Main JavaScript file for SIG Cafe Jogja

// Global variables
let currentMap = null;
let allCafes = [];
let filteredCafes = [];

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
async function initializeApp() {
    try {
        // Show loading indicator
        showLoadingIndicator();
        
        // Load initial data
        await loadCafeData();
        
        // Initialize components based on current page
        const currentPage = getCurrentPage();
        
        switch(currentPage) {
            case 'index':
                initializeDashboard();
                break;
            case 'map':
                initializeMapPage();
                break;
            case 'analysis':
                initializeAnalysisPage();
                break;
        }
        
        // Hide loading indicator
        hideLoadingIndicator();
        
        // Initialize tooltips and popovers
        initializeBootstrapComponents();
        
    } catch (error) {
        console.error('Error initializing application:', error);
        showErrorMessage('Gagal memuat aplikasi. Silakan refresh halaman.');
    }
}

// Get current page from URL
function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('map')) return 'map';
    if (path.includes('analysis')) return 'analysis';
    return 'index';
}

// Load cafe data from API
async function loadCafeData() {
    try {
        const response = await fetch('/api/cafes');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        allCafes = await response.json();
        filteredCafes = [...allCafes];
        
        console.log(`Loaded ${allCafes.length} cafes`);
        return allCafes;
        
    } catch (error) {
        console.error('Error loading cafe data:', error);
        throw error;
    }
}

// Initialize dashboard components
function initializeDashboard() {
    // Load statistics cards
    updateStatisticsCards();
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Load recent cafes table
    loadRecentCafesTable();
    
    // Add animation to cards
    animateCards();
}

// Initialize map page components
function initializeMapPage() {
    // Map-specific initialization
    initializeMapControls();
    loadMapFilters();
}

// Initialize analysis page components
function initializeAnalysisPage() {
    // Analysis-specific initialization
    if (typeof Chart !== 'undefined') {
        initializeAnalysisCharts();
    }
}

// Update statistics cards
async function updateStatisticsCards() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Update card values with animation
        animateCountUp('total-cafes', stats.total_cafes);
        animateCountUp('total-districts', Object.keys(stats.by_district).length);
        animateCountUp('total-types', Object.keys(stats.by_type).length);
        
        // Calculate and update average density
        const avgDensity = (stats.total_cafes / Object.keys(stats.by_district).length).toFixed(1);
        animateCountUp('avg-density', avgDensity, '/wilayah');
        
    } catch (error) {
        console.error('Error updating statistics:', error);
    }
}

// Animate count up effect
function animateCountUp(elementId, targetValue, suffix = '') {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const startValue = 0;
    const duration = 2000;
    const startTime = performance.now();
    
    function updateCount(currentTime) {
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        
        const currentValue = Math.floor(progress * targetValue);
        element.textContent = currentValue + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(updateCount);
        }
    }
    
    requestAnimationFrame(updateCount);
}

// Initialize Bootstrap components
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Initialize charts
async function initializeCharts() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Create district chart if element exists
        const districtChartElement = document.getElementById('districtChart');
        if (districtChartElement) {
            createDistrictChart(districtChartElement, stats.by_district);
        }
        
        // Create type chart if element exists
        const typeChartElement = document.getElementById('typeChart');
        if (typeChartElement) {
            createTypeChart(typeChartElement, stats.by_type);
        }
        
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}

// Create district distribution chart
function createDistrictChart(element, data) {
    const ctx = element.getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40'
                ],
                borderWidth: 3,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} cafe (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 2000
            }
        }
    });
}

// Create cafe type chart
function createTypeChart(element, data) {
    const ctx = element.getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Jumlah Cafe',
                data: Object.values(data),
                backgroundColor: [
                    'rgba(220, 53, 69, 0.8)',   // Traditional - Red
                    'rgba(13, 110, 253, 0.8)',  // Modern - Blue
                    'rgba(25, 135, 84, 0.8)'    // Chain - Green
                ],
                borderColor: [
                    'rgba(220, 53, 69, 1)',
                    'rgba(13, 110, 253, 1)',
                    'rgba(25, 135, 84, 1)'
                ],
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return `Cafe ${context[0].label}`;
                        },
                        label: function(context) {
                            return `Jumlah: ${context.parsed.y} cafe`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            weight: '500'
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: {
                            weight: '500'
                        }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Load recent cafes table
function loadRecentCafesTable() {
    const tableBody = document.getElementById('cafeTableBody');
    if (!tableBody) return;
    
    // Clear existing content
    tableBody.innerHTML = '';
    
    // Show loading
    const loadingRow = document.createElement('tr');
    loadingRow.innerHTML = '<td colspan="5" class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Memuat data...</td>';
    tableBody.appendChild(loadingRow);
    
    // Load data with delay for smooth animation
    setTimeout(() => {
        tableBody.innerHTML = '';
        
        // Show first 10 cafes
        const recentCafes = allCafes.slice(0, 10);
        
        recentCafes.forEach((cafe, index) => {
            const row = document.createElement('tr');
            row.style.opacity = '0';
            row.style.transform = 'translateY(20px)';
            
            row.innerHTML = `
                <td>
                    <strong>${cafe.name}</strong>
                    <br><small class="text-muted">${cafe.district}</small>
                </td>
                <td>
                    <span class="badge bg-primary">${cafe.district}</span>
                </td>
                <td>
                    <span class="badge bg-${getTypeColor(cafe.type)}">${cafe.type}</span>
                </td>
                <td>
                    <small class="text-muted">
                        ${cafe.lat.toFixed(4)}, ${cafe.lon.toFixed(4)}
                    </small>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="showCafeDetail('${cafe.name}')"
                            data-bs-toggle="tooltip" 
                            title="Lihat detail">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success ms-1" 
                            onclick="showOnMap(${cafe.lat}, ${cafe.lon})"
                            data-bs-toggle="tooltip" 
                            title="Lihat di peta">
                        <i class="fas fa-map-marker-alt"></i>
                    </button>
                </td>
            `;
            
            tableBody.appendChild(row);
            
            // Animate row appearance
            setTimeout(() => {
                row.style.transition = 'all 0.5s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, index * 100);
        });
        
        // Re-initialize tooltips for new elements
        initializeBootstrapComponents();
        
    }, 500);
}

// Get color class for cafe type
function getTypeColor(type) {
    const colors = {
        'Traditional': 'danger',
        'Modern': 'info',
        'Chain': 'success'
    };
    return colors[type] || 'secondary';
}

// Show cafe detail modal
function showCafeDetail(cafeName) {
    const cafe = allCafes.find(c => c.name === cafeName);
    
    if (!cafe) {
        showErrorMessage('Data cafe tidak ditemukan');
        return;
    }
    
    // Create and show modal
    const modalHtml = `
        <div class="modal fade" id="cafeDetailModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-coffee"></i> ${cafe.name}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-6"><strong>Nama Cafe:</strong></div>
                            <div class="col-6">${cafe.name}</div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6"><strong>Wilayah:</strong></div>
                            <div class="col-6"><span class="badge bg-primary">${cafe.district}</span></div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6"><strong>Jenis:</strong></div>
                            <div class="col-6"><span class="badge bg-${getTypeColor(cafe.type)}">${cafe.type}</span></div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6"><strong>Koordinat:</strong></div>
                            <div class="col-6">
                                <small class="text-muted">
                                    Lat: ${cafe.lat.toFixed(6)}<br>
                                    Lon: ${cafe.lon.toFixed(6)}
                                </small>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Tutup</button>
                        <button type="button" class="btn btn-primary" onclick="showOnMap(${cafe.lat}, ${cafe.lon})">
                            <i class="fas fa-map-marker-alt"></i> Lihat di Peta
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('cafeDetailModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('cafeDetailModal'));
    modal.show();
}

// Show cafe on map
function showOnMap(lat, lon) {
    // Open map page with coordinates
    const url = `/map?lat=${lat}&lon=${lon}`;
    window.open(url, '_blank');
}

// Animate cards on page load
function animateCards() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 150);
    });
}

// Show loading indicator
function showLoadingIndicator() {
    const loadingHtml = `
        <div id="globalLoading" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" 
             style="background: rgba(255,255,255,0.9); z-index: 9999;">
            <div class="text-center">
                <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h5>Memuat SIG Cafe Jogja...</h5>
                <p class="text-muted">Mohon tunggu sebentar</p>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

// Hide loading indicator
function hideLoadingIndicator() {
    const loading = document.getElementById('globalLoading');
    if (loading) {
        loading.style.transition = 'opacity 0.5s ease';
        loading.style.opacity = '0';
        
        setTimeout(() => {
            loading.remove();
        }, 500);
    }
}

// Show error message
function showErrorMessage(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="fas fa-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert-danger');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Show success message
function showSuccessMessage(message) {
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="fas fa-check-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert-success');
        if (alert) {
            alert.remove();
        }
    }, 3000);
}

// Initialize map controls (for map page)
function initializeMapControls() {
    // Map-specific control initialization
    console.log('Initializing map controls...');
}

// Load map filters (for map page)
function loadMapFilters() {
    // Load filter options for map page
    console.log('Loading map filters...');
}

// Initialize analysis charts (for analysis page)
function initializeAnalysisCharts() {
    // Analysis-specific chart initialization
    console.log('Initializing analysis charts...');
}

// Utility function to format numbers
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Utility function to calculate distance between two points
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// Export functions for global access
window.SIGCafeJogja = {
    loadCafeData,
    showCafeDetail,
    showOnMap,
    formatNumber,
    calculateDistance,
    showSuccessMessage,
    showErrorMessage
};
