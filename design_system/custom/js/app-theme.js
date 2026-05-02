(function () {
    const storageKey = 'maosNaObraTheme';
    const darkClasses = ['app-skin-dark', 'app-navigation-dark', 'app-header-dark'];
    const root = document.documentElement;
    const toggle = document.getElementById('themeToggle');

    function applyTheme(theme) {
        const isDark = theme === 'dark';
        darkClasses.forEach(function (className) {
            root.classList.toggle(className, isDark);
        });
        if (toggle) {
            toggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
            toggle.setAttribute('title', isDark ? 'Usar modo claro' : 'Usar modo escuro');
        }
    }

    const savedTheme = localStorage.getItem(storageKey);
    const preferredTheme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    applyTheme(savedTheme || preferredTheme);

    if (toggle) {
        toggle.addEventListener('click', function () {
            const nextTheme = root.classList.contains('app-skin-dark') ? 'light' : 'dark';
            localStorage.setItem(storageKey, nextTheme);
            applyTheme(nextTheme);
        });
    }
})();
