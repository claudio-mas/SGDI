/**
 * ============================================
 * SGDI - Animations JavaScript
 * Helpers for dynamic animations and loading states
 * ============================================
 */

(function() {
    'use strict';

    // ============================================
    // Loading Overlay Manager
    // ============================================
    window.GEDLoading = {
        /**
         * Show loading overlay
         */
        show: function(message = 'Carregando...') {
            let overlay = document.getElementById('globalLoadingOverlay');
            if (!overlay) {
                overlay = this.createOverlay();
            }
            const messageEl = overlay.querySelector('.loading-message');
            if (messageEl) {
                messageEl.textContent = message;
            }
            overlay.style.display = 'flex';
            setTimeout(() => overlay.classList.add('active'), 10);
        },

        /**
         * Hide loading overlay
         */
        hide: function() {
            const overlay = document.getElementById('globalLoadingOverlay');
            if (overlay) {
                overlay.classList.remove('active');
                setTimeout(() => overlay.style.display = 'none', 300);
            }
        },

        /**
         * Create overlay element if it doesn't exist
         */
        createOverlay: function() {
            const overlay = document.createElement('div');
            overlay.id = 'globalLoadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-overlay-content">
                    <div class="spinner-border text-light mb-3" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p class="text-light loading-message">Carregando...</p>
                </div>
            `;
            document.body.appendChild(overlay);
            return overlay;
        }
    };

    // ============================================
    // Button Loading State
    // ============================================
    window.GEDButton = {
        /**
         * Set button to loading state
         */
        setLoading: function(button, loadingText = 'Carregando...') {
            if (typeof button === 'string') {
                button = document.querySelector(button);
            }
            if (!button) return;

            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                ${loadingText}
            `;
            button.classList.add('btn-loading');
        },

        /**
         * Reset button from loading state
         */
        reset: function(button) {
            if (typeof button === 'string') {
                button = document.querySelector(button);
            }
            if (!button || !button.dataset.originalText) return;

            button.disabled = false;
            button.innerHTML = button.dataset.originalText;
            button.classList.remove('btn-loading');
            delete button.dataset.originalText;
        }
    };

    // ============================================
    // Animation Utilities
    // ============================================
    window.GEDAnimate = {
        /**
         * Add animation class to element
         */
        add: function(element, animationClass, callback) {
            if (typeof element === 'string') {
                element = document.querySelector(element);
            }
            if (!element) return;

            element.classList.add(animationClass);
            
            const handleAnimationEnd = () => {
                element.classList.remove(animationClass);
                element.removeEventListener('animationend', handleAnimationEnd);
                if (callback) callback();
            };

            element.addEventListener('animationend', handleAnimationEnd);
        },

        /**
         * Fade in element
         */
        fadeIn: function(element, callback) {
            this.add(element, 'fade-in', callback);
        },

        /**
         * Fade out element
         */
        fadeOut: function(element, callback) {
            this.add(element, 'fade-out', callback);
        },

        /**
         * Slide up element
         */
        slideUp: function(element, callback) {
            this.add(element, 'slide-up', callback);
        },

        /**
         * Scale in element
         */
        scaleIn: function(element, callback) {
            this.add(element, 'scale-in', callback);
        },

        /**
         * Shake element (for errors)
         */
        shake: function(element) {
            this.add(element, 'shake');
        },

        /**
         * Pulse element (for attention)
         */
        pulse: function(element) {
            this.add(element, 'pulse');
        },

        /**
         * Stagger animation for list items
         */
        staggerList: function(selector) {
            const items = document.querySelectorAll(selector);
            items.forEach((item, index) => {
                item.style.animationDelay = `${index * 0.1}s`;
                item.classList.add('stagger-item');
            });
        }
    };

    // ============================================
    // Skeleton Loader Manager
    // ============================================
    window.GEDSkeleton = {
        /**
         * Show skeleton in container
         */
        show: function(container, type = 'list', count = 3) {
            if (typeof container === 'string') {
                container = document.querySelector(container);
            }
            if (!container) return;

            container.dataset.originalContent = container.innerHTML;
            container.innerHTML = this.generate(type, count);
        },

        /**
         * Hide skeleton and restore content
         */
        hide: function(container) {
            if (typeof container === 'string') {
                container = document.querySelector(container);
            }
            if (!container || !container.dataset.originalContent) return;

            container.innerHTML = container.dataset.originalContent;
            delete container.dataset.originalContent;
        },

        /**
         * Generate skeleton HTML
         */
        generate: function(type, count) {
            let html = '';
            
            if (type === 'list') {
                for (let i = 0; i < count; i++) {
                    html += `
                        <div class="d-flex align-items-center mb-3 animate-pulse">
                            <div class="skeleton skeleton-avatar me-3"></div>
                            <div class="flex-grow-1">
                                <div class="skeleton skeleton-text mb-2" style="width: 70%;"></div>
                                <div class="skeleton skeleton-text" style="width: 40%;"></div>
                            </div>
                        </div>
                    `;
                }
            } else if (type === 'card') {
                html = `
                    <div class="card animate-pulse">
                        <div class="skeleton skeleton-image"></div>
                        <div class="card-body">
                            <div class="skeleton skeleton-text mb-2"></div>
                            <div class="skeleton skeleton-text mb-2"></div>
                            <div class="skeleton skeleton-text" style="width: 60%;"></div>
                        </div>
                    </div>
                `;
            } else if (type === 'table') {
                html = `
                    <table class="table animate-pulse">
                        <thead>
                            <tr>
                                ${Array(count).fill('<th><div class="skeleton skeleton-text"></div></th>').join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${Array(5).fill(`
                                <tr>
                                    ${Array(count).fill('<td><div class="skeleton skeleton-text"></div></td>').join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            
            return html;
        }
    };

    // ============================================
    // Toast Notifications (integrates with animations)
    // ============================================
    window.GEDToast = {
        /**
         * Show toast notification
         */
        show: function(message, type = 'info', duration = 5000) {
            const toast = this.create(message, type);
            document.body.appendChild(toast);
            
            // Trigger animation
            setTimeout(() => toast.classList.add('show', 'fade-in-down'), 10);
            
            // Auto hide
            setTimeout(() => {
                toast.classList.remove('show', 'fade-in-down');
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        },

        /**
         * Create toast element
         */
        create: function(message, type) {
            const icons = {
                success: 'bi-check-circle',
                error: 'bi-exclamation-triangle',
                warning: 'bi-exclamation-circle',
                info: 'bi-info-circle'
            };

            const toast = document.createElement('div');
            toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible position-fixed top-0 end-0 m-3`;
            toast.style.zIndex = '9999';
            toast.innerHTML = `
                <i class="bi ${icons[type] || icons.info} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            toast.querySelector('.btn-close').addEventListener('click', () => {
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 300);
            });

            return toast;
        }
    };

    // ============================================
    // Progress Tracker
    // ============================================
    window.GEDProgress = {
        /**
         * Update progress bar
         */
        update: function(selector, value, max = 100, animated = true) {
            const progressBar = document.querySelector(selector);
            if (!progressBar) return;

            const percentage = Math.round((value / max) * 100);
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', value);
            progressBar.textContent = `${percentage}%`;

            if (animated) {
                progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
            }
        },

        /**
         * Set progress to complete
         */
        complete: function(selector) {
            this.update(selector, 100, 100, false);
            const progressBar = document.querySelector(selector);
            if (progressBar) {
                progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
                progressBar.classList.add('bg-success');
            }
        }
    };

    // ============================================
    // Smooth Scroll
    // ============================================
    window.GEDScroll = {
        /**
         * Scroll to element smoothly
         */
        to: function(element, offset = 0) {
            if (typeof element === 'string') {
                element = document.querySelector(element);
            }
            if (!element) return;

            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        },

        /**
         * Scroll to top
         */
        toTop: function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
    };

    // ============================================
    // Auto-initialize
    // ============================================
    document.addEventListener('DOMContentLoaded', function() {
        // Auto disable submit buttons on form submit
        document.querySelectorAll('form[data-disable-on-submit]').forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    GEDButton.setLoading(submitBtn);
                }
            });
        });

        // Add ripple effect to buttons
        document.querySelectorAll('.btn:not(.no-ripple)').forEach(button => {
            button.classList.add('ripple');
        });

        // Animate alerts
        document.querySelectorAll('.alert').forEach(alert => {
            alert.classList.add('fade-in-down');
        });

        // Add hover effects to cards
        document.querySelectorAll('.card').forEach(card => {
            if (!card.classList.contains('no-hover')) {
                card.classList.add('hover-lift');
            }
        });

        // Stagger list items on pages that support it
        if (document.querySelector('[data-stagger-list]')) {
            const selector = document.querySelector('[data-stagger-list]').dataset.staggerList;
            GEDAnimate.staggerList(selector);
        }
    });

    // ============================================
    // Export to window
    // ============================================
    window.GED = window.GED || {};
    window.GED.Loading = GEDLoading;
    window.GED.Button = GEDButton;
    window.GED.Animate = GEDAnimate;
    window.GED.Skeleton = GEDSkeleton;
    window.GED.Toast = GEDToast;
    window.GED.Progress = GEDProgress;
    window.GED.Scroll = GEDScroll;

})();
