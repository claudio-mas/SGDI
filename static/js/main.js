/**
 * SGDI - Main JavaScript
 * Common utilities and functionality
 */

// ============================================
// Global Configuration
// ============================================
const GED = {
    config: {
        ajaxTimeout: 30000,
        toastDuration: 5000,
        debounceDelay: 300
    },
    
    // ============================================
    // Utility Functions
    // ============================================
    utils: {
        /**
         * Debounce function to limit function calls
         */
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        /**
         * Format file size in human-readable format
         */
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
        },
        
        /**
         * Format date in Brazilian format
         */
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        /**
         * Get file extension from filename
         */
        getFileExtension: function(filename) {
            return filename.split('.').pop().toLowerCase();
        },
        
        /**
         * Validate file type
         */
        isValidFileType: function(filename, allowedTypes) {
            const ext = this.getFileExtension(filename);
            return allowedTypes.includes(ext);
        },
        
        /**
         * Copy text to clipboard
         */
        copyToClipboard: function(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    GED.ui.showToast('Copiado!', 'Texto copiado para a área de transferência', 'success');
                }).catch(() => {
                    GED.ui.showToast('Erro', 'Não foi possível copiar o texto', 'danger');
                });
            } else {
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                try {
                    document.execCommand('copy');
                    GED.ui.showToast('Copiado!', 'Texto copiado para a área de transferência', 'success');
                } catch (err) {
                    GED.ui.showToast('Erro', 'Não foi possível copiar o texto', 'danger');
                }
                document.body.removeChild(textarea);
            }
        }
    },
    
    // ============================================
    // UI Functions
    // ============================================
    ui: {
        /**
         * Show loading overlay
         */
        showLoading: function(message = 'Carregando...') {
            let overlay = $('#loadingOverlay');
            if (overlay.length === 0) {
                overlay = $('<div>', {
                    id: 'loadingOverlay',
                    class: 'loading-overlay',
                    html: `
                        <div class="loading-overlay-content">
                            <div class="spinner-border text-light" role="status">
                                <span class="visually-hidden">Carregando...</span>
                            </div>
                            <p class="text-light mt-3">${message}</p>
                        </div>
                    `
                });
                $('body').append(overlay);
            }
            overlay.fadeIn(200);
        },
        
        /**
         * Hide loading overlay
         */
        hideLoading: function() {
            $('#loadingOverlay').fadeOut(200);
        },
        
        /**
         * Show toast notification
         */
        showToast: function(title, message, type = 'info') {
            const toastId = 'toast-' + Date.now();
            const toast = $(`
                <div class="toast align-items-center text-bg-${type} border-0" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            <strong>${title}</strong><br>
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `);
            
            let toastContainer = $('#toastContainer');
            if (toastContainer.length === 0) {
                toastContainer = $('<div>', {
                    id: 'toastContainer',
                    class: 'toast-container position-fixed top-0 end-0 p-3',
                    style: 'z-index: 9999;'
                });
                $('body').append(toastContainer);
            }
            
            toastContainer.append(toast);
            const bsToast = new bootstrap.Toast(toast[0], {
                autohide: true,
                delay: GED.config.toastDuration
            });
            bsToast.show();
            
            // Remove toast element after it's hidden
            toast.on('hidden.bs.toast', function() {
                $(this).remove();
            });
        },
        
        /**
         * Show confirmation dialog
         */
        confirm: function(title, message, onConfirm, onCancel) {
            const modalId = 'confirmModal-' + Date.now();
            const modal = $(`
                <div class="modal fade" id="${modalId}" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p>${message}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                                <button type="button" class="btn btn-primary" id="${modalId}-confirm">Confirmar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `);
            
            $('body').append(modal);
            const bsModal = new bootstrap.Modal(modal[0]);
            
            $(`#${modalId}-confirm`).on('click', function() {
                bsModal.hide();
                if (typeof onConfirm === 'function') {
                    onConfirm();
                }
            });
            
            modal.on('hidden.bs.modal', function() {
                if (typeof onCancel === 'function') {
                    onCancel();
                }
                $(this).remove();
            });
            
            bsModal.show();
        }
    },
    
    // ============================================
    // AJAX Functions
    // ============================================
    ajax: {
        /**
         * Make AJAX request with error handling
         */
        request: function(url, options = {}) {
            const defaults = {
                method: 'GET',
                dataType: 'json',
                timeout: GED.config.ajaxTimeout,
                beforeSend: function() {
                    if (options.showLoading !== false) {
                        GED.ui.showLoading();
                    }
                },
                complete: function() {
                    if (options.showLoading !== false) {
                        GED.ui.hideLoading();
                    }
                },
                error: function(xhr, status, error) {
                    let errorMessage = 'Ocorreu um erro ao processar sua solicitação.';
                    
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMessage = xhr.responseJSON.error;
                    } else if (status === 'timeout') {
                        errorMessage = 'A solicitação expirou. Tente novamente.';
                    } else if (status === 'abort') {
                        errorMessage = 'A solicitação foi cancelada.';
                    } else if (xhr.status === 403) {
                        errorMessage = 'Você não tem permissão para realizar esta ação.';
                    } else if (xhr.status === 404) {
                        errorMessage = 'Recurso não encontrado.';
                    } else if (xhr.status === 500) {
                        errorMessage = 'Erro interno do servidor. Tente novamente mais tarde.';
                    }
                    
                    GED.ui.showToast('Erro', errorMessage, 'danger');
                    
                    if (typeof options.error === 'function') {
                        options.error(xhr, status, error);
                    }
                }
            };
            
            const settings = $.extend({}, defaults, options);
            return $.ajax(url, settings);
        }
    },
    
    // ============================================
    // Form Validation
    // ============================================
    validation: {
        /**
         * Validate form before submission
         */
        validateForm: function(formElement) {
            const form = $(formElement);
            let isValid = true;
            
            // Clear previous validation messages
            form.find('.is-invalid').removeClass('is-invalid');
            form.find('.invalid-feedback').remove();
            
            // Check required fields
            form.find('[required]').each(function() {
                const field = $(this);
                if (!field.val() || field.val().trim() === '') {
                    isValid = false;
                    field.addClass('is-invalid');
                    field.after('<div class="invalid-feedback">Este campo é obrigatório.</div>');
                }
            });
            
            // Validate email fields
            form.find('input[type="email"]').each(function() {
                const field = $(this);
                const email = field.val();
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                
                if (email && !emailRegex.test(email)) {
                    isValid = false;
                    field.addClass('is-invalid');
                    field.after('<div class="invalid-feedback">Digite um e-mail válido.</div>');
                }
            });
            
            // Validate password confirmation
            const password = form.find('input[name="password"]');
            const confirmPassword = form.find('input[name="confirm_password"]');
            
            if (password.length && confirmPassword.length) {
                if (password.val() !== confirmPassword.val()) {
                    isValid = false;
                    confirmPassword.addClass('is-invalid');
                    confirmPassword.after('<div class="invalid-feedback">As senhas não coincidem.</div>');
                }
            }
            
            return isValid;
        },
        
        /**
         * Real-time field validation
         */
        setupRealTimeValidation: function(formElement) {
            const form = $(formElement);
            
            form.find('input, textarea, select').on('blur', function() {
                const field = $(this);
                field.removeClass('is-invalid');
                field.next('.invalid-feedback').remove();
                
                if (field.prop('required') && (!field.val() || field.val().trim() === '')) {
                    field.addClass('is-invalid');
                    field.after('<div class="invalid-feedback">Este campo é obrigatório.</div>');
                }
                
                if (field.attr('type') === 'email' && field.val()) {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(field.val())) {
                        field.addClass('is-invalid');
                        field.after('<div class="invalid-feedback">Digite um e-mail válido.</div>');
                    }
                }
            });
        }
    },
    
    // ============================================
    // File Upload Handling
    // ============================================
    upload: {
        /**
         * Handle file selection and preview
         */
        handleFileSelect: function(inputElement, previewContainer, options = {}) {
            const input = $(inputElement);
            const container = $(previewContainer);
            const allowedTypes = options.allowedTypes || ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'];
            const maxSize = options.maxSize || 52428800; // 50MB default
            
            input.on('change', function(e) {
                const files = e.target.files;
                container.empty();
                
                if (files.length === 0) return;
                
                Array.from(files).forEach(file => {
                    // Validate file type
                    const ext = GED.utils.getFileExtension(file.name);
                    if (!allowedTypes.includes(ext)) {
                        GED.ui.showToast('Erro', `Tipo de arquivo não permitido: ${ext}`, 'danger');
                        return;
                    }
                    
                    // Validate file size
                    if (file.size > maxSize) {
                        GED.ui.showToast('Erro', `Arquivo muito grande: ${file.name}. Tamanho máximo: ${GED.utils.formatFileSize(maxSize)}`, 'danger');
                        return;
                    }
                    
                    // Create preview
                    const preview = $(`
                        <div class="file-preview-item card mb-2">
                            <div class="card-body d-flex align-items-center">
                                <i class="bi bi-file-earmark fs-3 me-3 text-primary"></i>
                                <div class="flex-grow-1">
                                    <div class="fw-bold">${file.name}</div>
                                    <small class="text-muted">${GED.utils.formatFileSize(file.size)}</small>
                                </div>
                                <button type="button" class="btn btn-sm btn-outline-danger remove-file">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                            </div>
                        </div>
                    `);
                    
                    preview.find('.remove-file').on('click', function() {
                        preview.remove();
                        input.val('');
                    });
                    
                    container.append(preview);
                });
            });
        },
        
        /**
         * Upload file with progress
         */
        uploadWithProgress: function(formData, url, progressCallback, successCallback, errorCallback) {
            $.ajax({
                url: url,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                xhr: function() {
                    const xhr = new window.XMLHttpRequest();
                    xhr.upload.addEventListener('progress', function(e) {
                        if (e.lengthComputable) {
                            const percentComplete = (e.loaded / e.total) * 100;
                            if (typeof progressCallback === 'function') {
                                progressCallback(percentComplete);
                            }
                        }
                    }, false);
                    return xhr;
                },
                success: function(response) {
                    if (typeof successCallback === 'function') {
                        successCallback(response);
                    }
                },
                error: function(xhr, status, error) {
                    if (typeof errorCallback === 'function') {
                        errorCallback(xhr, status, error);
                    } else {
                        GED.ui.showToast('Erro', 'Falha no upload do arquivo', 'danger');
                    }
                }
            });
        }
    }
};

// ============================================
// Document Ready
// ============================================
$(document).ready(function() {
    console.log('SGDI initialized');
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    $('.alert:not(.alert-permanent)').each(function() {
        const alert = $(this);
        setTimeout(function() {
            alert.fadeOut(300, function() {
                $(this).remove();
            });
        }, 5000);
    });
    
    // Confirm delete actions
    $('[data-confirm-delete]').on('click', function(e) {
        e.preventDefault();
        const link = $(this);
        const message = link.data('confirm-delete') || 'Tem certeza que deseja excluir este item?';
        
        GED.ui.confirm(
            'Confirmar Exclusão',
            message,
            function() {
                window.location.href = link.attr('href');
            }
        );
    });
    
    // Setup real-time validation for forms with class 'needs-validation'
    $('form.needs-validation').each(function() {
        GED.validation.setupRealTimeValidation(this);
    });
    
    // Handle form submission with validation
    $('form.needs-validation').on('submit', function(e) {
        if (!GED.validation.validateForm(this)) {
            e.preventDefault();
            e.stopPropagation();
            GED.ui.showToast('Erro', 'Por favor, corrija os erros no formulário', 'danger');
        }
    });
    
    // Copy to clipboard functionality
    $('[data-copy-text]').on('click', function() {
        const text = $(this).data('copy-text');
        GED.utils.copyToClipboard(text);
    });
    
    // Back to top button
    const backToTop = $('<button>', {
        id: 'backToTop',
        class: 'btn btn-primary rounded-circle position-fixed',
        style: 'bottom: 20px; right: 20px; display: none; z-index: 1000; width: 50px; height: 50px;',
        html: '<i class="bi bi-arrow-up"></i>'
    });
    
    $('body').append(backToTop);
    
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            backToTop.fadeIn();
        } else {
            backToTop.fadeOut();
        }
    });
    
    backToTop.on('click', function() {
        $('html, body').animate({ scrollTop: 0 }, 600);
    });
});

// Export GED object to global scope
window.GED = GED;
