// Main JavaScript file for CEAF Farmácia

// Global variables
let searchModal;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize Bootstrap modal
    const searchModalElement = document.getElementById('searchModal');
    if (searchModalElement) {
        searchModal = new bootstrap.Modal(searchModalElement);
    }
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize scroll to top button
    initializeScrollToTop();
    
    // Add fade-in animation to cards
    animateCards();
}

function initializeSearch() {
    // Main search form
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('searchInput').value.trim();
            if (query) {
                searchConditions(query);
            }
        });
    }
    
    // Quick search input
    const quickSearchInput = document.getElementById('quickSearch');
    if (quickSearchInput) {
        quickSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    searchConditions(query);
                }
            }
        });
    }
}

function searchConditions(query) {
    if (!query.trim()) {
        return;
    }
    
    // Show modal and loading state
    if (searchModal) {
        const resultsContainer = document.getElementById('searchResults');
        resultsContainer.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Buscando...</span>
                </div>
                <p class="mt-2 text-muted">Buscando por "${query}"...</p>
            </div>
        `;
        searchModal.show();
    }
    
    // Perform search
    fetch(`/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data, query);
        })
        .catch(error => {
            console.error('Search error:', error);
            displaySearchError(error.message);
        });
}

function displaySearchResults(data, query) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h5>Nenhum resultado encontrado</h5>
                <p class="text-muted">
                    Não encontramos condições que correspondam a "${query}".
                </p>
                <div class="alert alert-info text-start mt-3">
                    <h6><i class="fas fa-lightbulb me-2"></i>Dicas de busca:</h6>
                    <ul class="mb-0 small">
                        <li>Nomes populares: <strong>espinhas</strong> (acne), <strong>açúcar alto</strong> (diabetes), <strong>tremor</strong> (parkinson)</li>
                        <li>Abreviações: <strong>TEA</strong> (autismo), <strong>TDAH</strong> (déficit de atenção), <strong>DM</strong> (diabetes)</li>
                        <li>Mesmo com erros: <strong>alzeimer</strong>, <strong>diabetis</strong>, <strong>parkison</strong></li>
                        <li>Sintomas: <strong>esquecimento</strong>, <strong>falta de ar</strong>, <strong>coceira</strong></li>
                    </ul>
                </div>
                <div class="mt-3">
                    <button class="btn btn-outline-primary" onclick="searchModal.hide()">
                        Tentar nova busca
                    </button>
                    <a href="/" class="btn btn-primary ms-2">
                        Ver todas as condições
                    </a>
                </div>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="mb-3 d-flex justify-content-between align-items-center">
            <h6 class="text-muted mb-0">
                ${data.total} resultado${data.total !== 1 ? 's' : ''} para "${query}"
            </h6>
            ${data.source === 'ai_enhanced' ? 
                '<span class="badge bg-success"><i class="fas fa-brain me-1"></i>IA</span>' : 
                data.source === 'cache' ? 
                '<span class="badge bg-info"><i class="fas fa-bolt me-1"></i>Cache</span>' : ''
            }
        </div>
    `;
    
    data.results.forEach(condition => {
        html += `
            <div class="search-result-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <a href="/condition/${encodeURIComponent(condition.name)}" 
                           class="search-result-title">
                            <i class="fas fa-file-medical me-2"></i>
                            ${condition.name}
                        </a>
                        ${condition.description ? `
                            <p class="text-muted small mt-1 mb-0">
                                ${condition.description.substring(0, 150)}${condition.description.length > 150 ? '...' : ''}
                            </p>
                        ` : ''}
                    </div>
                    <div class="ms-3">
                        <a href="/condition/${encodeURIComponent(condition.name)}" 
                           class="btn btn-outline-primary btn-sm">
                            Ver Detalhes
                        </a>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    
    // Add click tracking for analytics (if needed)
    trackSearch(query, data.total);
}

function displaySearchError(errorMessage) {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = `
        <div class="text-center">
            <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
            <h5>Erro na busca</h5>
            <p class="text-muted">
                Ocorreu um erro ao realizar a busca: ${errorMessage}
            </p>
            <button class="btn btn-primary" onclick="searchModal.hide()">
                Tentar novamente
            </button>
        </div>
    `;
}

function initializeScrollToTop() {
    // Create scroll to top button
    const scrollButton = document.createElement('button');
    scrollButton.className = 'scroll-to-top';
    scrollButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollButton.setAttribute('aria-label', 'Voltar ao topo');
    document.body.appendChild(scrollButton);
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            scrollButton.classList.add('show');
        } else {
            scrollButton.classList.remove('show');
        }
    });
    
    // Smooth scroll to top
    scrollButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

function animateCards() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
}

function trackSearch(query, resultCount) {
    // Analytics tracking (can be extended with Google Analytics, etc.)
    console.log(`Search: "${query}" - ${resultCount} results`);
    
    // Example: Send to analytics service
    // gtag('event', 'search', {
    //     search_term: query,
    //     result_count: resultCount
    // });
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Auto-complete functionality (can be enhanced)
function initializeAutoComplete() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="buscar"], input[placeholder*="Buscar"]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length > 2) {
                // Could implement auto-complete suggestions here
                console.log('Auto-complete for:', query);
            }
        }, 300));
    });
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    // Could send error reports to monitoring service
});

// Service worker registration (for offline functionality)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Uncomment when service worker is implemented
        // navigator.serviceWorker.register('/static/sw.js')
        //     .then(registration => console.log('SW registered'))
        //     .catch(error => console.log('SW registration failed'));
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('searchInput') || document.getElementById('quickSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        if (searchModal && searchModal._isShown) {
            searchModal.hide();
        }
    }
});

// Touch device optimizations
if ('ontouchstart' in window) {
    document.body.classList.add('touch-device');
    
    // Improve button feedback on touch devices
    document.addEventListener('touchstart', function() {}, true);
}

// Accessibility improvements
function improveAccessibility() {
    // Add skip to content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Pular para o conteúdo principal';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: #000;
        color: #fff;
        padding: 8px;
        text-decoration: none;
        z-index: 9999;
    `;
    skipLink.addEventListener('focus', function() {
        this.style.top = '6px';
    });
    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main landmark
    const main = document.querySelector('main');
    if (main && !main.id) {
        main.id = 'main';
    }
}

// Initialize accessibility improvements
document.addEventListener('DOMContentLoaded', improveAccessibility);

// New search functions for medications and CID-10
function performQuickSearch() {
    const query = document.getElementById('quickSearch').value.trim();
    if (query) {
        searchConditions(query);
    }
}

function performMedicationSearch() {
    const query = document.getElementById('medicationSearch').value.trim();
    if (query) {
        searchByMedication(query);
    }
}

function performCidSearch() {
    const query = document.getElementById('cidSearch').value.trim();
    if (query) {
        searchByCid(query);
    }
}

function searchByMedication(medication) {
    if (!medication.trim()) {
        return;
    }
    
    // Show modal and loading state
    if (searchModal) {
        const resultsContainer = document.getElementById('searchResults');
        resultsContainer.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-success" role="status">
                    <span class="visually-hidden">Buscando...</span>
                </div>
                <p class="mt-2 text-muted">Buscando condições para o medicamento "${medication}"...</p>
            </div>
        `;
        searchModal.show();
    }
    
    // Perform medication search
    fetch(`/search/medication?q=${encodeURIComponent(medication)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data, medication, 'medicamento');
        })
        .catch(error => {
            console.error('Medication search error:', error);
            displaySearchError(error.message);
        });
}

function searchByCid(cid) {
    if (!cid.trim()) {
        return;
    }
    
    // Show modal and loading state
    if (searchModal) {
        const resultsContainer = document.getElementById('searchResults');
        resultsContainer.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-info" role="status">
                    <span class="visually-hidden">Buscando...</span>
                </div>
                <p class="mt-2 text-muted">Buscando condições para o CID-10 "${cid}"...</p>
            </div>
        `;
        searchModal.show();
    }
    
    // Perform CID search
    fetch(`/search/cid?q=${encodeURIComponent(cid)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data, cid, 'CID-10');
        })
        .catch(error => {
            console.error('CID search error:', error);
            displaySearchError(error.message);
        });
}

// Enhanced search results display
function displaySearchResults(data, query, searchType = 'condição') {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h5>Nenhum resultado encontrado</h5>
                <p class="text-muted">
                    Não encontramos condições que correspondam a "${query}" para ${searchType}.
                </p>
                <div class="alert alert-info text-start mt-3">
                    <h6><i class="fas fa-lightbulb me-2"></i>Dicas de busca:</h6>
                    <ul class="mb-0 small">
                        ${searchType === 'medicamento' ? `
                            <li>Nome genérico: <strong>adalimumab</strong>, <strong>rituximab</strong>, <strong>metotrexato</strong></li>
                            <li>Nome comercial: <strong>Humira</strong>, <strong>Remicade</strong>, <strong>Enbrel</strong></li>
                        ` : searchType === 'CID-10' ? `
                            <li>Código completo: <strong>M05.9</strong>, <strong>L70.0</strong>, <strong>E10.9</strong></li>
                            <li>Código parcial: <strong>M05</strong>, <strong>L70</strong>, <strong>E10</strong></li>
                        ` : `
                            <li>Nomes populares: <strong>espinhas</strong> (acne), <strong>açúcar alto</strong> (diabetes)</li>
                            <li>Abreviações: <strong>TEA</strong> (autismo), <strong>TDAH</strong> (déficit de atenção)</li>
                        `}
                    </ul>
                </div>
                <div class="mt-3">
                    <button class="btn btn-outline-primary" onclick="searchModal.hide()">
                        Tentar nova busca
                    </button>
                    <a href="/" class="btn btn-primary ms-2">
                        Ver todas as condições
                    </a>
                </div>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="mb-3 d-flex justify-content-between align-items-center">
            <h6 class="text-muted mb-0">
                ${data.total} resultado${data.total !== 1 ? 's' : ''} para ${searchType} "${query}"
            </h6>
            ${data.source === 'ai_enhanced' ? 
                '<span class="badge bg-success"><i class="fas fa-brain me-1"></i>IA</span>' : 
                data.source === 'cache' ? 
                '<span class="badge bg-info"><i class="fas fa-bolt me-1"></i>Cache</span>' : ''
            }
        </div>
    `;
    
    data.results.forEach(condition => {
        let extraInfo = '';
        
        // Show medications if searching by medication
        if (searchType === 'medicamento' && condition.medicamentos) {
            const matchingMeds = condition.medicamentos.filter(med => 
                med.toLowerCase().includes(query.toLowerCase())
            );
            if (matchingMeds.length > 0) {
                extraInfo = `
                    <div class="mt-2">
                        <span class="badge bg-success me-1">
                            <i class="fas fa-pills me-1"></i>
                            ${matchingMeds.slice(0, 2).join(', ')}
                            ${matchingMeds.length > 2 ? ` +${matchingMeds.length - 2}` : ''}
                        </span>
                    </div>
                `;
            }
        }
        
        // Show CID-10 if searching by CID
        if (searchType === 'CID-10' && condition.cid_10) {
            const matchingCids = condition.cid_10.filter(cid => 
                cid.toLowerCase().includes(query.toLowerCase())
            );
            if (matchingCids.length > 0) {
                extraInfo = `
                    <div class="mt-2">
                        <span class="badge bg-info me-1">
                            <i class="fas fa-code me-1"></i>
                            ${matchingCids.slice(0, 2).join(', ')}
                            ${matchingCids.length > 2 ? ` +${matchingCids.length - 2}` : ''}
                        </span>
                    </div>
                `;
            }
        }
        
        html += `
            <div class="search-result-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <a href="/condition/${encodeURIComponent(condition.name)}" 
                           class="search-result-title">
                            <i class="fas fa-file-medical me-2"></i>
                            ${condition.name}
                        </a>
                        ${condition.description ? `
                            <p class="text-muted small mt-1 mb-0">
                                ${condition.description.substring(0, 150)}${condition.description.length > 150 ? '...' : ''}
                            </p>
                        ` : ''}
                        ${extraInfo}
                    </div>
                    <div class="ms-3">
                        <a href="/condition/${encodeURIComponent(condition.name)}" 
                           class="btn btn-outline-primary btn-sm">
                            Ver Detalhes
                        </a>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    
    // Add click tracking for analytics (if needed)
    trackSearch(query, data.total, searchType);
}

// Example search functions
function searchExample(query) {
    document.getElementById('quickSearch').value = query;
    performQuickSearch();
}

function searchMedicationExample(medication) {
    document.getElementById('medicationSearch').value = medication;
    performMedicationSearch();
}

function searchCidExample(cid) {
    document.getElementById('cidSearch').value = cid;
    performCidSearch();
}

// Enhanced tracking with search type
function trackSearch(query, resultCount, searchType = 'condition') {
    console.log(`${searchType} search: "${query}" - ${resultCount} results`);
    
    // Example: Send to analytics service
    // gtag('event', 'search', {
    //     search_term: query,
    //     search_type: searchType,
    //     result_count: resultCount
    // });
}

// Initialize new search inputs
function initializeNewSearchInputs() {
    // Medication search input
    const medicationSearchInput = document.getElementById('medicationSearch');
    if (medicationSearchInput) {
        medicationSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    searchByMedication(query);
                }
            }
        });
    }
    
    // CID search input
    const cidSearchInput = document.getElementById('cidSearch');
    if (cidSearchInput) {
        cidSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    searchByCid(query);
                }
            }
        });
    }
}

// Update initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeNewSearchInputs();
});

// Export functions for global use
window.searchConditions = searchConditions;
window.displaySearchResults = displaySearchResults;
window.performQuickSearch = performQuickSearch;
window.performMedicationSearch = performMedicationSearch;
window.performCidSearch = performCidSearch;
window.searchExample = searchExample;
window.searchMedicationExample = searchMedicationExample;
window.searchCidExample = searchCidExample;