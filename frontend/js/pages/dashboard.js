/**
 * Fleet Management - Dashboard Page
 * Handles dashboard statistics display.
 */

import { api, handleApiError } from '../main.js';

/**
 * Initialize the dashboard page.
 */
async function initDashboard() {
  await loadStats();
}

/**
 * Load and display statistics from the stats endpoint.
 */
async function loadStats() {
  try {
    const response = await api.stats.get();
    updateStatsDisplay(response.data);
  } catch (error) {
    console.warn('Could not load stats:', error.message);
    handleApiError(error);
    displayPlaceholderStats();
  }
}

/**
 * Update all statistics displays from the API response.
 * @param {Object} data - Statistics data from API.
 */
function updateStatsDisplay(data) {
  const vehicleCounts = data.vehicle_count_by_status || {};
  const driverCounts = data.driver_count_by_status || {};

  // Calculate totals
  const totalVehicles = Object.values(vehicleCounts).reduce((sum, n) => sum + n, 0);
  const totalDrivers = Object.values(driverCounts).reduce((sum, n) => sum + n, 0);

  // Update vehicle stats
  document.getElementById('vehicleCount').textContent = totalVehicles;
  document.getElementById('vehiclesActive').textContent = vehicleCounts.active || 0;
  document.getElementById('vehiclesInactive').textContent = vehicleCounts.inactive || 0;
  document.getElementById('vehiclesMaintenance').textContent = vehicleCounts.maintenance || 0;
  document.getElementById('maintenanceCount').textContent = vehicleCounts.maintenance || 0;

  // Update driver stats
  document.getElementById('driverCount').textContent = totalDrivers;
  document.getElementById('driversActive').textContent = driverCounts.active || 0;
  document.getElementById('driversSuspended').textContent = driverCounts.suspended || 0;

  // Update assignment stats
  document.getElementById('activeAssignments').textContent = data.active_assignments_count || 0;
}

/**
 * Display placeholder stats when API is unavailable.
 */
function displayPlaceholderStats() {
  document.getElementById('vehicleCount').textContent = '0';
  document.getElementById('driverCount').textContent = '0';
  document.getElementById('activeAssignments').textContent = '0';
  document.getElementById('maintenanceCount').textContent = '0';
  document.getElementById('vehiclesActive').textContent = '0';
  document.getElementById('vehiclesInactive').textContent = '0';
  document.getElementById('vehiclesMaintenance').textContent = '0';
  document.getElementById('driversActive').textContent = '0';
  document.getElementById('driversSuspended').textContent = '0';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initDashboard);
