(function () {
    const storageKey = 'maosNaObraTheme';
    const darkClasses = ['app-skin-dark', 'app-navigation-dark', 'app-header-dark'];
    const root = document.documentElement;
    const toggle = document.getElementById('themeToggle');
    const profileToggle = document.getElementById('profileDropdownToggle');
    const profileMenu = document.getElementById('profileDropdownMenu');
    const profileState = {
        isOpen: false,
    };

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

    if (profileToggle && profileMenu) {
        function getMenuLeft() {
            const toggleRect = profileToggle.getBoundingClientRect();
            const menuWidth = profileMenu.offsetWidth || 260;
            const viewportPadding = 12;
            const preferredLeft = toggleRect.right - menuWidth;
            const maxLeft = window.innerWidth - menuWidth - viewportPadding;
            return Math.max(viewportPadding, Math.min(preferredLeft, maxLeft));
        }

        function positionMenu() {
            profileMenu.style.left = `${getMenuLeft()}px`;
            profileMenu.style.top = `${Math.max(12, profileToggle.getBoundingClientRect().bottom + 10)}px`;
            profileMenu.style.right = 'auto';
        }

        function openMenu() {
            profileState.isOpen = true;
            profileMenu.hidden = false;
            profileMenu.classList.add('is-open');
            document.body.appendChild(profileMenu);
            positionMenu();
            profileToggle.setAttribute('aria-expanded', 'true');
        }

        function closeMenu() {
            if (!profileState.isOpen) {
                return;
            }
            profileState.isOpen = false;
            profileMenu.classList.remove('is-open');
            profileMenu.hidden = true;
            profileToggle.setAttribute('aria-expanded', 'false');
        }

        profileToggle.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            if (profileState.isOpen) {
                closeMenu();
                return;
            }
            openMenu();
        });

        document.addEventListener('click', function (event) {
            if (!profileState.isOpen) {
                return;
            }
            if (profileMenu.contains(event.target) || profileToggle.contains(event.target)) {
                return;
            }
            closeMenu();
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                closeMenu();
            }
        });

        window.addEventListener('resize', function () {
            if (profileState.isOpen) {
                positionMenu();
            }
        });

        window.addEventListener('scroll', function () {
            if (profileState.isOpen) {
                positionMenu();
            }
        }, true);
    }

})();
