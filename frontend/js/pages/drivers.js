/**
 * Fleet Management - Drivers Page
 * Handles driver CRUD operations.
 */

import {
    api,
    clearForm,
    createStatusBadge,
    getFormData,
    handleApiError,
    initModal,
    populateForm,
    showToast,
} from '../main.js';

// State
let currentPage = 0;
const pageSize = 50;
let editingDriverId = null;
let editingDriverEtag = null;
let deletingDriverId = null;

// Modal instances
let driverModal;
let deleteModal;

/**
 * Initialize the drivers page.
 */
function initDriversPage() {
  // Initialize modals
  driverModal = initModal('driverModal');
  deleteModal = initModal('deleteModal');

  // Event listeners
  document.getElementById('addDriverBtn')?.addEventListener('click', openAddModal);
  document.getElementById('driverForm')?.addEventListener('submit', handleFormSubmit);
  document.getElementById('confirmDelete')?.addEventListener('click', handleDeleteConfirm);
  document.getElementById('statusFilter')?.addEventListener('change', () => loadDrivers(0));
  document.getElementById('prevPage')?.addEventListener('click', () => loadDrivers(currentPage - 1));
  document.getElementById('nextPage')?.addEventListener('click', () => loadDrivers(currentPage + 1));

  // Initial load
  loadDrivers(0);
}

/**
 * Load drivers from API.
 * @param {number} page - Page number to load.
 */
async function loadDrivers(page = 0) {
  const tbody = document.getElementById('driversTableBody');
  tbody.innerHTML = '<tr class="loading-row"><td colspan="5">Loading drivers...</td></tr>';

  try {
    const status = document.getElementById('statusFilter')?.value;

    const response = await api.drivers.list({
      status: status || undefined,
      limit: pageSize,
      skip: page * pageSize,
    });

    currentPage = page;
    renderDrivers(response.data);
    updatePagination(response.pagination);
  } catch (error) {
    handleApiError(error);
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5">Failed to load drivers</td></tr>';
  }
}

/**
 * Render drivers in the table.
 * @param {Array} drivers - List of drivers.
 */
function renderDrivers(drivers) {
  const tbody = document.getElementById('driversTableBody');

  if (!drivers || drivers.length === 0) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No drivers found</td></tr>';
    return;
  }

  tbody.innerHTML = drivers.map(driver => `
    <tr data-id="${driver.id}">
      <td><strong>${escapeHtml(driver.name)}</strong></td>
      <td>${escapeHtml(driver.license_number)}</td>
      <td>${escapeHtml(driver.contact_number)}</td>
      <td>${createStatusBadge(driver.status)}</td>
      <td class="actions-cell">
        <button class="btn btn-sm btn-secondary" onclick="editDriver('${driver.id}')" 
                aria-label="Edit driver">Edit</button>
        <button class="btn btn-sm btn-danger" onclick="deleteDriver('${driver.id}', '${escapeHtml(driver.name)}')" 
                aria-label="Delete driver">Delete</button>
      </td>
    </tr>
  `).join('');
}

/**
 * Update pagination controls.
 * @param {Object} pagination - Pagination info.
 */
function updatePagination(pagination) {
  if (!pagination) return;

  const prevBtn = document.getElementById('prevPage');
  const nextBtn = document.getElementById('nextPage');
  const info = document.getElementById('paginationInfo');

  const totalPages = Math.ceil(pagination.total / pagination.limit);
  const currentPageNum = Math.floor(pagination.skip / pagination.limit) + 1;

  prevBtn.disabled = currentPage === 0;
  nextBtn.disabled = !pagination.has_more;
  info.textContent = `Page ${currentPageNum} of ${totalPages || 1}`;
}

/**
 * Open modal to add a new driver.
 */
function openAddModal() {
  editingDriverId = null;
  editingDriverEtag = null;
  document.getElementById('modalTitle').textContent = 'Add Driver';
  clearForm(document.getElementById('driverForm'));
  driverModal.open();
}

/**
 * Open modal to edit a driver.
 * @param {string} id - Driver ID.
 */
async function editDriver(id) {
  try {
    const response = await api.drivers.get(id);
    editingDriverId = id;
    editingDriverEtag = response._etag;
    
    document.getElementById('modalTitle').textContent = 'Edit Driver';
    populateForm(document.getElementById('driverForm'), response.data);
    driverModal.open();
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Open delete confirmation modal.
 * @param {string} id - Driver ID.
 * @param {string} name - Driver name for display.
 */
function deleteDriver(id, name) {
  deletingDriverId = id;
  document.getElementById('deleteDriverInfo').textContent = `Name: ${name}`;
  deleteModal.open();
}

/**
 * Handle form submission.
 * @param {Event} event - Submit event.
 */
async function handleFormSubmit(event) {
  event.preventDefault();
  
  const form = event.target;
  const data = getFormData(form);

  try {
    if (editingDriverId) {
      await api.drivers.update(editingDriverId, data, editingDriverEtag);
      showToast('Driver updated successfully', 'success');
    } else {
      await api.drivers.create(data);
      showToast('Driver created successfully', 'success');
    }
    
    driverModal.close();
    loadDrivers(currentPage);
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Handle delete confirmation.
 */
async function handleDeleteConfirm() {
  if (!deletingDriverId) return;

  try {
    await api.drivers.delete(deletingDriverId);
    showToast('Driver deleted successfully', 'success');
    deleteModal.close();
    loadDrivers(currentPage);
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Escape HTML to prevent XSS.
 * @param {string} str - String to escape.
 * @returns {string} - Escaped string.
 */
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Make functions available globally for onclick handlers
window.editDriver = editDriver;
window.deleteDriver = deleteDriver;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initDriversPage);
