/* Theme Manager for Singlecore Apps */

frappe.provide('singlecore_apps.theme');

singlecore_apps.theme = {
    init: function () {
        this.apply_saved_theme();
        // Wait a bit for the navbar to be fully rendered
        setTimeout(() => this.add_theme_switcher(), 1000);
    },

    apply_saved_theme: function () {
        const savedTheme = localStorage.getItem('singlecore_apps_theme') || 'default';
        this.set_theme(savedTheme);
    },

    set_theme: function (themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('singlecore_apps_theme', themeName);

        // Update body class for potential Frappe styling overrides
        $('body').removeClass('theme-success theme-ocean').addClass('theme-' + themeName);

        console.log(`[Singlecore Apps] Applied theme: ${themeName}`);
        frappe.show_alert({ message: `Theme changed to: ${themeName}`, indicator: 'green' }, 3);
    },

    add_theme_switcher: function () {
        // Remove existing if any
        $('#theme-switcher-item').remove();

        // Try multiple navbar selectors for different Frappe versions
        let $nav = $('.navbar-right');
        if (!$nav.length) $nav = $('.navbar .container-fluid > .nav:last');
        if (!$nav.length) $nav = $('#navbar-breadcrumbs').parent();
        if (!$nav.length) $nav = $('header .container-fluid');

        if ($nav.length) {
            const switcherHtml = `
                <div id="theme-switcher-item" style="position: fixed; top: 10px; right: 120px; z-index: 9999;">
                    <div class="dropdown">
                        <button class="btn btn-sm btn-default dropdown-toggle" type="button" data-toggle="dropdown" title="Switch Theme" style="background: #eee; border-radius: 5px;">
                            🎨 Theme
                        </button>
                        <div class="dropdown-menu dropdown-menu-right">
                            <a class="dropdown-item" href="javascript:singlecore_apps.theme.set_theme('default')">⬜ Standard</a>
                            <a class="dropdown-item" href="javascript:singlecore_apps.theme.set_theme('success')">🟢 Success (Green)</a>
                            <a class="dropdown-item" href="javascript:singlecore_apps.theme.set_theme('ocean')">🔵 Ocean (Blue)</a>
                        </div>
                    </div>
                </div>
            `;
            $('body').append(switcherHtml);
            console.log('[Singlecore Apps] Theme switcher added to page');
        } else {
            console.warn('[Singlecore Apps] Could not find navbar to attach theme switcher');
        }
    }
};

$(document).on('toolbar_setup', function () {
    singlecore_apps.theme.init();
});

// Fallback init - try after page ready
$(document).ready(function () {
    setTimeout(() => singlecore_apps.theme.init(), 2000);
});
