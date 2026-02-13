/**
 * Fleet Management - Vehicles Page
 * Handles vehicle CRUD operations.
 */

import {
    api,
    clearForm,
    createStatusBadge,
    getFormData,
    handleApiError,
    initModal,
    populateForm,
    showToast
} from '../main.js';

// State
let currentPage = 0;
const pageSize = 50;
let editingVehicleId = null;
let editingVehicleEtag = null;
let deletingVehicleId = null;

// Modal instances
let vehicleModal;
let deleteModal;

/**
 * Initialize the vehicles page.
 */
function initVehiclesPage() {
  // Initialize modals
  vehicleModal = initModal('vehicleModal');
  deleteModal = initModal('deleteModal');

  // Event listeners
  document.getElementById('addVehicleBtn')?.addEventListener('click', openAddModal);
  document.getElementById('vehicleForm')?.addEventListener('submit', handleFormSubmit);
  document.getElementById('confirmDelete')?.addEventListener('click', handleDeleteConfirm);
  document.getElementById('statusFilter')?.addEventListener('change', () => loadVehicles(0));
  document.getElementById('typeFilter')?.addEventListener('change', () => loadVehicles(0));
  document.getElementById('prevPage')?.addEventListener('click', () => loadVehicles(currentPage - 1));
  document.getElementById('nextPage')?.addEventListener('click', () => loadVehicles(currentPage + 1));

  // Initial load
  loadVehicles(0);
}

/**
 * Load vehicles from API.
 * @param {number} page - Page number to load.
 */
async function loadVehicles(page = 0) {
  const tbody = document.getElementById('vehiclesTableBody');
  tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Loading vehicles...</td></tr>';

  try {
    const status = document.getElementById('statusFilter')?.value;
    const type = document.getElementById('typeFilter')?.value;

    const response = await api.vehicles.list({
      status: status || undefined,
      type: type || undefined,
      limit: pageSize,
      skip: page * pageSize,
    });

    currentPage = page;
    renderVehicles(response.data);
    updatePagination(response.pagination);
  } catch (error) {
    handleApiError(error);
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Failed to load vehicles</td></tr>';
  }
}

/**
 * Render vehicles in the table.
 * @param {Array} vehicles - List of vehicles.
 */
function renderVehicles(vehicles) {
  const tbody = document.getElementById('vehiclesTableBody');

  if (!vehicles || vehicles.length === 0) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No vehicles found</td></tr>';
    return;
  }

  tbody.innerHTML = vehicles.map(vehicle => `
    <tr data-id="${vehicle.id}">
      <td><strong>${escapeHtml(vehicle.plate_number)}</strong></td>
      <td>${escapeHtml(vehicle.model)}</td>
      <td>${vehicle.year}</td>
      <td>${vehicle.type}</td>
      <td>${vehicle.fuel_type}</td>
      <td>${createStatusBadge(vehicle.status)}</td>
      <td class="actions-cell">
        <button class="btn btn-sm btn-secondary" onclick="editVehicle('${vehicle.id}')" 
                aria-label="Edit vehicle">Edit</button>
        <button class="btn btn-sm btn-danger" onclick="deleteVehicle('${vehicle.id}', '${escapeHtml(vehicle.plate_number)}')" 
                aria-label="Delete vehicle">Delete</button>
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
 * Open modal to add a new vehicle.
 */
function openAddModal() {
  editingVehicleId = null;
  editingVehicleEtag = null;
  document.getElementById('modalTitle').textContent = 'Add Vehicle';
  clearForm(document.getElementById('vehicleForm'));
  vehicleModal.open();
}

/**
 * Open modal to edit a vehicle.
 * @param {string} id - Vehicle ID.
 */
async function editVehicle(id) {
  try {
    const response = await api.vehicles.get(id);
    editingVehicleId = id;
    editingVehicleEtag = response._etag;
    
    document.getElementById('modalTitle').textContent = 'Edit Vehicle';
    populateForm(document.getElementById('vehicleForm'), response.data);
    vehicleModal.open();
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Open delete confirmation modal.
 * @param {string} id - Vehicle ID.
 * @param {string} plateNumber - Vehicle plate number for display.
 */
function deleteVehicle(id, plateNumber) {
  deletingVehicleId = id;
  document.getElementById('deleteVehicleInfo').textContent = `Plate: ${plateNumber}`;
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
    if (editingVehicleId) {
      await api.vehicles.update(editingVehicleId, data, editingVehicleEtag);
      showToast('Vehicle updated successfully', 'success');
    } else {
      await api.vehicles.create(data);
      showToast('Vehicle created successfully', 'success');
    }
    
    vehicleModal.close();
    loadVehicles(currentPage);
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Handle delete confirmation.
 */
async function handleDeleteConfirm() {
  if (!deletingVehicleId) return;

  try {
    await api.vehicles.delete(deletingVehicleId);
    showToast('Vehicle deleted successfully', 'success');
    deleteModal.close();
    loadVehicles(currentPage);
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
window.editVehicle = editVehicle;
window.deleteVehicle = deleteVehicle;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initVehiclesPage);
