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

// Export functions for global use
window.searchConditions = searchConditions;
window.displaySearchResults = displaySearchResults;