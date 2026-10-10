(function() {
    function getSavedTheme() {
        return localStorage.getItem('ms_theme') || 'amber';
    }
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('ms_theme', theme);
        const label = document.getElementById('themeName');
        if (label) {
            label.textContent = theme === 'amber' ? 'Cyber Theme' : 'Amber Theme';
        }
    }
    window.toggleTheme = function() {
        const current = getSavedTheme();
        const next = current === 'amber' ? 'cyber' : 'amber';
        applyTheme(next);
    };
    // Apply immediately to prevent flash
    applyTheme(getSavedTheme());
    document.addEventListener('DOMContentLoaded', function() {
        applyTheme(getSavedTheme());
    });
})();
