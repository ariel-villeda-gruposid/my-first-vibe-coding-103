/**
 * Fleet Management - API Client
 * Handles all HTTP communication with the backend API.
 */

const API_BASE_URL = '/api/v1';

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(code, message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

/**
 * Make an HTTP request to the API.
 * @param {string} endpoint - API endpoint path.
 * @param {Object} options - Fetch options.
 * @returns {Promise<Object>} - Response data.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  // Add ETag header if provided
  if (options.etag) {
    config.headers['If-Match'] = options.etag;
    delete config.etag;
  }

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        data.error?.code || 'UNKNOWN_ERROR',
        data.error?.message || 'An unknown error occurred',
        response.status,
        data.error?.details
      );
    }

    // Return data with ETag if present
    const result = {
      ...data,
      _etag: response.headers.get('ETag'),
    };

    return result;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('NETWORK_ERROR', 'Failed to connect to the server', 0);
  }
}

/**
 * API client methods organized by resource.
 */
export const api = {
  /**
   * Health check endpoint.
   */
  health: {
    check: () => request('/health'),
  },

  /**
   * Vehicle endpoints.
   */
  vehicles: {
    list: (params = {}) => {
      const query = new URLSearchParams();
      if (params.status) query.set('status', params.status);
      if (params.type) query.set('type', params.type);
      if (params.limit) query.set('limit', params.limit);
      if (params.skip) query.set('skip', params.skip);
      const queryString = query.toString();
      return request(`/vehicles${queryString ? `?${queryString}` : ''}`);
    },

    get: (id) => request(`/vehicles/${id}`),

    create: (data) => request('/vehicles', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

    update: (id, data, etag = null) => request(`/vehicles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      etag,
    }),

    patch: (id, data, etag = null) => request(`/vehicles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
      etag,
    }),

    delete: (id) => request(`/vehicles/${id}`, {
      method: 'DELETE',
    }),
  },

  /**
   * Driver endpoints.
   */
  drivers: {
    list: (params = {}) => {
      const query = new URLSearchParams();
      if (params.status) query.set('status', params.status);
      if (params.limit) query.set('limit', params.limit);
      if (params.skip) query.set('skip', params.skip);
      const queryString = query.toString();
      return request(`/drivers${queryString ? `?${queryString}` : ''}`);
    },

    get: (id) => request(`/drivers/${id}`),

    create: (data) => request('/drivers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

    update: (id, data, etag = null) => request(`/drivers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      etag,
    }),

    patch: (id, data, etag = null) => request(`/drivers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
      etag,
    }),

    delete: (id) => request(`/drivers/${id}`, {
      method: 'DELETE',
    }),
  },

  /**
   * Assignment endpoints.
   */
  assignments: {
    list: (params = {}) => {
      const query = new URLSearchParams();
      if (params.active !== undefined) query.set('active', params.active);
      if (params.limit) query.set('limit', params.limit);
      if (params.skip) query.set('skip', params.skip);
      const queryString = query.toString();
      return request(`/assignments${queryString ? `?${queryString}` : ''}`);
    },

    get: (id) => request(`/assignments/${id}`),

    create: (data) => request('/assignments', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

    update: (id, data) => request(`/assignments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

    close: (id) => request(`/assignments/${id}/close`, {
      method: 'POST',
    }),
  },

  /**
   * Statistics endpoint.
   */
  stats: {
    get: () => request('/stats'),
  },
};

export default api;
