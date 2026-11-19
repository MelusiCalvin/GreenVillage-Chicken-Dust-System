/**
 * ChickenHub - Main JavaScript
 * Handles responsive sidebar toggling, notification alerts and UI interactions.
 */

document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------------------
    // 1. Dashboard Mobile Sidebar Toggle
    // -------------------------------------------------------------------------
    const sidebarToggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.dashboard-sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('sidebar-open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            if (sidebar) {
                sidebar.classList.remove('sidebar-open');
            }
            sidebarOverlay.classList.remove('active');
        });
    }

    // -------------------------------------------------------------------------
    // 2. Auto-dismiss alerts after 6 seconds (excluding danger/error alerts)
    // -------------------------------------------------------------------------
    const autoDismissAlerts = document.querySelectorAll('.alert:not(.alert-danger)');
    autoDismissAlerts.forEach(function (alert) {
        setTimeout(function () {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 6000);
    });

    // -------------------------------------------------------------------------
    // 3. Tooltips Initialization
    // -------------------------------------------------------------------------
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
