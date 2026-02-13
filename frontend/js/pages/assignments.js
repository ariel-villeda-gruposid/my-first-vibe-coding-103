/**
 * Fleet Management - Assignments Page
 * Handles assignment CRUD operations.
 */

import {
    api,
    clearForm,
    formatDate,
    formatDateForInput,
    getFormData,
    handleApiError,
    initModal,
    showToast,
} from '../main.js';

// State
let currentPage = 0;
const pageSize = 50;
let editingAssignmentId = null;
let closingAssignmentId = null;
let driversCache = [];
let vehiclesCache = [];

// Modal instances
let assignmentModal;
let closeModal;

/**
 * Initialize the assignments page.
 */
function initAssignmentsPage() {
  // Initialize modals
  assignmentModal = initModal('assignmentModal');
  closeModal = initModal('closeModal');

  // Event listeners
  document.getElementById('addAssignmentBtn')?.addEventListener('click', openAddModal);
  document.getElementById('assignmentForm')?.addEventListener('submit', handleFormSubmit);
  document.getElementById('confirmClose')?.addEventListener('click', handleCloseConfirm);
  document.getElementById('activeFilter')?.addEventListener('change', () => loadAssignments(0));
  document.getElementById('prevPage')?.addEventListener('click', () => loadAssignments(currentPage - 1));
  document.getElementById('nextPage')?.addEventListener('click', () => loadAssignments(currentPage + 1));

  // Initial load
  loadAssignments(0);
  loadDropdownData();
}

/**
 * Load drivers and vehicles for dropdowns.
 */
async function loadDropdownData() {
  try {
    console.log('Loading dropdown data...');
    const [driversResponse, vehiclesResponse] = await Promise.all([
      api.drivers.list({ status: 'active', limit: 100 }),
      api.vehicles.list({ status: 'active', limit: 100 }),
    ]);

    console.log('Drivers response:', driversResponse);
    console.log('Vehicles response:', vehiclesResponse);

    driversCache = driversResponse.data || [];
    vehiclesCache = vehiclesResponse.data || [];

    console.log('Drivers cache:', driversCache.length, 'items');
    console.log('Vehicles cache:', vehiclesCache.length, 'items');

    populateDriverDropdown();
    populateVehicleDropdown();
  } catch (error) {
    console.error('Could not load dropdown data:', error);
  }
}

/**
 * Populate driver dropdown.
 */
function populateDriverDropdown() {
  const select = document.getElementById('driver');
  console.log('Populating driver dropdown, select element:', select);
  if (!select) return;

  const options = driversCache.map(driver => 
    `<option value="${driver.id}">${escapeHtml(driver.name)} (${escapeHtml(driver.license_number)})</option>`
  ).join('');
  console.log('Driver options HTML:', options.substring(0, 200) + '...');
  
  select.innerHTML = '<option value="">Select driver</option>' + options;
}

/**
 * Populate vehicle dropdown.
 */
function populateVehicleDropdown() {
  const select = document.getElementById('vehicle');
  console.log('Populating vehicle dropdown, select element:', select);
  if (!select) return;

  const options = vehiclesCache.map(vehicle => 
    `<option value="${vehicle.id}">${escapeHtml(vehicle.plate_number)} - ${escapeHtml(vehicle.model)}</option>`
  ).join('');
  console.log('Vehicle options HTML:', options.substring(0, 200) + '...');

  select.innerHTML = '<option value="">Select vehicle</option>' + options;
}

/**
 * Load assignments from API.
 * @param {number} page - Page number to load.
 */
async function loadAssignments(page = 0) {
  const tbody = document.getElementById('assignmentsTableBody');
  tbody.innerHTML = '<tr class="loading-row"><td colspan="7">Loading assignments...</td></tr>';

  try {
    const activeFilter = document.getElementById('activeFilter')?.value;

    const params = {
      limit: pageSize,
      skip: page * pageSize,
    };

    if (activeFilter === 'active') {
      params.active = true;
    } else if (activeFilter === 'closed') {
      params.active = false;
    }

    const response = await api.assignments.list(params);

    currentPage = page;
    renderAssignments(response.data);
    updatePagination(response.pagination);
  } catch (error) {
    handleApiError(error);
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Failed to load assignments</td></tr>';
  }
}

/**
 * Render assignments in the table.
 * @param {Array} assignments - List of assignments.
 */
function renderAssignments(assignments) {
  const tbody = document.getElementById('assignmentsTableBody');

  if (!assignments || assignments.length === 0) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No assignments found</td></tr>';
    return;
  }

  tbody.innerHTML = assignments.map(assignment => {
    const isActive = !assignment.end_datetime || new Date(assignment.end_datetime) >= new Date();
    const statusBadge = isActive 
      ? '<span class="status-badge status-active">Active</span>'
      : '<span class="status-badge status-closed">Closed</span>';

    // Find driver and vehicle names from cache
    const driver = driversCache.find(d => d.id === assignment.driver_id);
    const vehicle = vehiclesCache.find(v => v.id === assignment.vehicle_id);

    const driverName = driver ? driver.name : assignment.driver_id;
    const vehiclePlate = vehicle ? vehicle.plate_number : assignment.vehicle_id;

    return `
      <tr data-id="${assignment.id}">
        <td>${escapeHtml(driverName)}</td>
        <td>${escapeHtml(vehiclePlate)}</td>
        <td>${formatDate(assignment.start_datetime)}</td>
        <td>${assignment.end_datetime ? formatDate(assignment.end_datetime) : '-'}</td>
        <td>${escapeHtml(assignment.notes || '-')}</td>
        <td>${statusBadge}</td>
        <td class="actions-cell">
          ${isActive ? `
            <button class="btn btn-sm btn-warning" onclick="closeAssignment('${assignment.id}')" 
                    aria-label="Close assignment">Close</button>
          ` : ''}
        </td>
      </tr>
    `;
  }).join('');
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
 * Open modal to add a new assignment.
 */
async function openAddModal() {
  editingAssignmentId = null;
  document.getElementById('modalTitle').textContent = 'Create Assignment';
  clearForm(document.getElementById('assignmentForm'));
  
  // Ensure dropdowns are populated
  if (driversCache.length === 0 || vehiclesCache.length === 0) {
    await loadDropdownData();
  }
  populateDriverDropdown();
  populateVehicleDropdown();
  
  // Set default start time to now
  const now = new Date();
  document.getElementById('startDatetime').value = formatDateForInput(now);
  
  assignmentModal.open();
}

/**
 * Open close confirmation modal.
 * @param {string} id - Assignment ID.
 */
function closeAssignment(id) {
  closingAssignmentId = id;
  document.getElementById('closeAssignmentInfo').textContent = '';
  closeModal.open();
}

/**
 * Handle form submission.
 * @param {Event} event - Submit event.
 */
async function handleFormSubmit(event) {
  event.preventDefault();
  
  const form = event.target;
  const data = getFormData(form);

  // Convert datetime fields to ISO format
  if (data.start_datetime) {
    data.start_datetime = new Date(data.start_datetime).toISOString();
  }
  if (data.end_datetime) {
    data.end_datetime = new Date(data.end_datetime).toISOString();
  }

  try {
    await api.assignments.create(data);
    showToast('Assignment created successfully', 'success');
    
    assignmentModal.close();
    loadAssignments(currentPage);
    loadDropdownData(); // Refresh available drivers/vehicles
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Handle close confirmation.
 */
async function handleCloseConfirm() {
  if (!closingAssignmentId) return;

  try {
    await api.assignments.close(closingAssignmentId);
    showToast('Assignment closed successfully', 'success');
    closeModal.close();
    loadAssignments(currentPage);
    loadDropdownData(); // Refresh available drivers/vehicles
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
window.closeAssignment = closeAssignment;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initAssignmentsPage);
