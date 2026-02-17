// Theme Switcher
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
const themeText = document.getElementById('themeText');
const html = document.documentElement;

// Load theme from localStorage
let savedTheme = 'dark';
try { savedTheme = localStorage.getItem('theme') || 'dark'; } catch(e) {}
html.setAttribute('data-theme', savedTheme);
updateThemeUI(savedTheme);

// Theme toggle handler
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        html.setAttribute('data-theme', newTheme);
        try { localStorage.setItem('theme', newTheme); } catch(e) {}
        updateThemeUI(newTheme);
    });
}

function updateThemeUI(theme) {
    if (themeIcon && themeText) {
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-moon';
            themeText.textContent = 'Dark Mode';
        } else {
            themeIcon.className = 'fas fa-sun';
            themeText.textContent = 'Light Mode';
        }
    }
}

// Settings page theme selector
const themeSelect = document.getElementById('themeSelect');
if (themeSelect) {
    themeSelect.value = savedTheme;
    themeSelect.addEventListener('change', (e) => {
        const newTheme = e.target.value;
        html.setAttribute('data-theme', newTheme);
        try { localStorage.setItem('theme', newTheme); } catch(e) {}
        updateThemeUI(newTheme);
    });
}
