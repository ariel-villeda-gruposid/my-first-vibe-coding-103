/**
 * Fleet Management - Main JavaScript Entry Point
 * Shared utilities and initialization.
 */

import { api, ApiError } from './api.js';

/**
 * Show a toast notification.
 * @param {string} message - Message to display.
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'.
 * @param {number} duration - Duration in milliseconds.
 */
export function showToast(message, type = 'info', duration = 3000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast alert alert-${type}`;
  toast.textContent = message;
  toast.setAttribute('role', 'alert');
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Handle API errors and display appropriate messages.
 * @param {Error} error - The error to handle.
 */
export function handleApiError(error) {
  if (error instanceof ApiError) {
    let message = error.message;
    
    // Handle validation errors with field details
    if (error.details) {
      const fieldErrors = Object.entries(error.details)
        .map(([field, errors]) => `${field}: ${errors.map(e => e.message).join(', ')}`)
        .join('; ');
      message = `${message} - ${fieldErrors}`;
    }
    
    showToast(message, 'error');
  } else {
    showToast('An unexpected error occurred', 'error');
    console.error('Unexpected error:', error);
  }
}

/**
 * Format a date string to locale format.
 * @param {string} dateString - ISO date string.
 * @returns {string} - Formatted date.
 */
export function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a date for datetime-local input.
 * @param {string|Date} date - Date to format.
 * @returns {string} - Formatted date string for input.
 */
export function formatDateForInput(date) {
  if (!date) return '';
  const d = new Date(date);
  return d.toISOString().slice(0, 16);
}

/**
 * Initialize modal functionality.
 * @param {string} modalId - The modal element ID.
 * @returns {Object} - Modal control methods.
 */
export function initModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return null;

  const closeButtons = modal.querySelectorAll('[data-close-modal]');
  
  const open = () => {
    modal.hidden = false;
    modal.querySelector('.modal-content')?.focus();
    document.body.style.overflow = 'hidden';
  };

  const close = () => {
    modal.hidden = true;
    document.body.style.overflow = '';
  };

  // Close on overlay/button click
  closeButtons.forEach(btn => {
    btn.addEventListener('click', close);
  });

  // Close on Escape key
  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });

  return { open, close, element: modal };
}

/**
 * Get form data as an object.
 * @param {HTMLFormElement} form - The form element.
 * @returns {Object} - Form data as key-value pairs.
 */
export function getFormData(form) {
  const formData = new FormData(form);
  const data = {};
  
  for (const [key, value] of formData.entries()) {
    // Skip empty values
    if (value === '') continue;
    
    // Convert numeric fields
    if (['year', 'limit', 'skip'].includes(key)) {
      data[key] = parseInt(value, 10);
    } else {
      data[key] = value.trim();
    }
  }
  
  return data;
}

/**
 * Populate a form with data.
 * @param {HTMLFormElement} form - The form element.
 * @param {Object} data - Data to populate.
 */
export function populateForm(form, data) {
  for (const [key, value] of Object.entries(data)) {
    const field = form.elements[key];
    if (field) {
      if (field.type === 'datetime-local') {
        field.value = formatDateForInput(value);
      } else {
        field.value = value ?? '';
      }
    }
  }
}

/**
 * Clear a form.
 * @param {HTMLFormElement} form - The form element.
 */
export function clearForm(form) {
  form.reset();
}

/**
 * Debounce a function.
 * @param {Function} func - Function to debounce.
 * @param {number} wait - Wait time in milliseconds.
 * @returns {Function} - Debounced function.
 */
export function debounce(func, wait = 300) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Create a status badge HTML.
 * @param {string} status - Status value.
 * @returns {string} - HTML string for the badge.
 */
export function createStatusBadge(status) {
  const statusLower = status.toLowerCase();
  return `<span class="status-badge status-${statusLower}">${status}</span>`;
}

// Export API client for use in page scripts
export { api, ApiError };

