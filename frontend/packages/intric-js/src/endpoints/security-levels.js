/**
 * @typedef {Object} SecurityLevel
 * @property {string} id
 * @property {string} name
 * @property {string | null} description
 * @property {number} value
 */

/**
 * @param {import('../client/client').Client} client Provide a client with which to call the endpoints
 */
export function initSecurityLevels(client) {
  return {
    /**
     * Get all security levels
     * @returns {Promise<SecurityLevel[]>}
     */
    getSecurityLevels: async () => {
      const res = await client.fetch("/api/v1/security-levels", {
        method: "get"
      });
      return res;
    },

    /**
     * Create a new security level
     * @param {Omit<SecurityLevel, 'id'>} securityLevel
     * @returns {Promise<SecurityLevel>}
     */
    createSecurityLevel: (securityLevel) =>
      client.fetch("/api/v1/security-levels", {
        method: "post",
        requestBody: { "application/json": securityLevel }
      }),

    /**
     * Update a security level
     * @param {string} id
     * @param {Partial<Omit<SecurityLevel, 'id'>>} securityLevel
     * @returns {Promise<SecurityLevel>}
     */
    updateSecurityLevel: (id, securityLevel) =>
      client.fetch(`/api/v1/security-levels/{id}`, {
        method: "patch",
        params: { path: { id } },
        requestBody: { "application/json": securityLevel }
      }),

    /**
     * Delete a security level
     * @param {string} id
     * @returns {Promise<void>}
     */
    deleteSecurityLevel: (id) =>
      client.fetch(`/api/v1/security-levels/{id}`, {
        method: "delete",
        params: { path: { id } }
      })
  };
}
