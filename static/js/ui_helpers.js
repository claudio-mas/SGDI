// Small UI helpers: disable submit buttons on submit, focus flash messages and alerts for screen readers
document.addEventListener('DOMContentLoaded', function() {
    // Disable submit buttons on forms with data-disable-on-submit to avoid double submit
    document.querySelectorAll('form[data-disable-on-submit="true"]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            // If form has already been submitted (disabled button), do nothing
            const submitBtn = form.querySelector('[type="submit"], button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Add spinner if not already present
                try {
                    const spinner = document.createElement('span');
                    spinner.className = 'spinner-border spinner-border-sm me-2';
                    spinner.setAttribute('role', 'status');
                    spinner.setAttribute('aria-hidden', 'true');
                    submitBtn.prepend(spinner);
                } catch (err) {
                    // ignore
                }
                if (submitBtn) submitBtn.disabled = true;
            }
        }, {passive: true});
    });

    // Focus newly added flash messages for screen readers
    const flashContainer = document.getElementById('flash-messages-container');
    if (flashContainer) {
        // Make container focusable
        flashContainer.setAttribute('tabindex', '-1');

        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (flashContainer.children.length > 0) {
                    // Focus the container so screen-readers announce new messages
                    try { flashContainer.focus({preventScroll: true}); } catch (e) { flashContainer.focus(); }

                    // Also focus the first alert inside if possible
                    const firstAlert = flashContainer.querySelector('.alert[role="alert"]');
                    if (firstAlert) {
                        try { firstAlert.focus({preventScroll:true}); } catch(e) { firstAlert.focus(); }
                    }
                }
            });
        });

        observer.observe(flashContainer, { childList: true, subtree: false });

        // If there are already messages on load, focus them
        if (flashContainer.children.length > 0) {
            try { flashContainer.focus({preventScroll: true}); } catch (e) { flashContainer.focus(); }
        }
    }

    // Ensure alert elements are focusable so JS can move focus to them
    document.querySelectorAll('.alert[role="alert"]').forEach(function(a) {
        if (!a.hasAttribute('tabindex')) a.setAttribute('tabindex', '-1');
    });
});
