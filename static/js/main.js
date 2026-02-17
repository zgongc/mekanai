// Main JavaScript for MekanAI

// Notification system
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // TODO: Implement toast notification UI
}

// Credit management
function updateCredits() {
    const creditElement = document.getElementById('creditCount');
    if (creditElement) {
        // TODO: Fetch from backend
        creditElement.textContent = '68';
    }
}

// Mobile menu toggle
function initMobileMenu() {
    const menuBtn = document.getElementById('mobileMenuBtn');
    const leftNav = document.querySelector('.left-nav');
    const overlay = document.getElementById('mobileOverlay');

    if (!menuBtn || !leftNav || !overlay) return;

    // Toggle menu
    menuBtn.addEventListener('click', () => {
        leftNav.classList.toggle('mobile-open');
        overlay.classList.toggle('active');
    });

    // Close menu when clicking overlay
    overlay.addEventListener('click', () => {
        leftNav.classList.remove('mobile-open');
        overlay.classList.remove('active');
    });

    // Close menu when clicking nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                leftNav.classList.remove('mobile-open');
                overlay.classList.remove('active');
            }
        });
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            leftNav.classList.remove('mobile-open');
            overlay.classList.remove('active');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initMobileMenu();
    updateCredits();
    console.log('MekanAI initialized');
    console.log('RTX 3090 ready for AI generation');
});

// Preset card click handlers
document.querySelectorAll('.preset-card').forEach(card => {
    card.addEventListener('click', function() {
        const presetName = this.querySelector('p').textContent;
        console.log(`Preset selected: ${presetName}`);
        showNotification(`"${presetName}" presetini uyguluyor...`, 'info');
        // TODO: Apply preset to current image
    });
});

// Project card handlers
document.querySelectorAll('.project-card').forEach(card => {
    if (!card.classList.contains('new-project')) {
        card.addEventListener('click', function() {
            const projectName = this.querySelector('h3').textContent;
            console.log(`Opening project: ${projectName}`);
            // TODO: Load project
        });
    }
});

// API helper functions
async function callAPI(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showNotification('Bir hata oluştu', 'error');
        return null;
    }
}

// Export for use in other scripts
window.MekanAI = {
    showNotification,
    updateCredits,
    callAPI
};
