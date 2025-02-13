/** @typedef {import('../client/client').IntricError} IntricError */
/** @typedef {import('../types/resources').User} User */
/** @typedef {import('../types/resources').UserSparse} UserSparse */
/** @typedef {import('../types/resources').Tenant} Tenant */

/**
 * @param {import('../client/client').Client} client Provide a client with which to call the endpoints
 */
export function initUser(client) {
  return {
    /**
     * Get info about the currently logged in user.
     * @returns {Promise<import('../types/schema').components["schemas"]["UserPublic"]>}
     * @throws {IntricError}
     * */
    me: async () => {
      const res = await client.fetch("/api/v1/users/me/", { method: "get" });
      return res;
    },

    /**
     * Get info about the currently logged in user's tenant.
     * @returns {Promise<Tenant>}
     * @throws {IntricError}
     * */
    tenant: async () => {
      const res = await client.fetch("/api/v1/users/tenant/", { method: "get" });
      return res;
    },

    /**
     * Generate a new api-key for the currently logged in user.
     * WARNING: Will delete any old api-key!
     * @returns {Promise<{truncated_key: string; key: string;}>}
     * @throws {IntricError}
     * */
    generateApiKey: async () => {
      const res = await client.fetch("/api/v1/users/api-keys/", { method: "get" });
      return res;
    },

    /**
     * Lists all users on this tenant.
     * @overload `{includeDetails: true}` requires super user privileges.
     * @param {{includeDetails: true}} params
     * @return {Promise<User[]>}
     *
     * @overload
     * @param {{includeDetails: false}} [params]
     * @return {Promise<UserSparse[]>}
     *
     * @param {{includeDetails: boolean}} [params]
     * @throws {IntricError}
     * */
    list: async (params) => {
      if (params && params.includeDetails) {
        const res = await client.fetch("/api/v1/admin/users/", { method: "get" });
        return res.items;
      }

      const res = await client.fetch("/api/v1/users/", { method: "get" });
      return res.items;
    },

    /**
     * Registers a new user for the current tenant. Requires super user privileges.
     * @param {import('../types/fetch').JSONRequestBody<"post", "/api/v1/admin/users/">} user
     * @returns {Promise<User>} Returns the created user
     * @throws {IntricError}
     * */
    create: async (user) => {
      const res = await client.fetch("/api/v1/admin/users/", {
        method: "post",
        requestBody: {
          "application/json": user
        }
      });
      return res;
    },

    /**
     * "Invites" a new user for the current tenant. This will create a new user without activating it.
     * It is a prerequisite to be able to login via zitadel. On first zitadel login the user will become active.
     * The Requires super user privileges.
     * @param {import('../types/fetch').JSONRequestBody<"post", "/api/v1/users/admin/invite/">} user
     * @returns {Promise<User>} Returns the invited user
     * @throws {IntricError}
     * */
    invite: async (user) => {
      const res = await client.fetch("/api/v1/users/admin/invite/", {
        method: "post",
        requestBody: { "application/json": user }
      });
      return res;
    },

    /**
     * Delete an user by id. Requires super user privileges.
     * @param {{id: string}} user User to delete
     * @returns {Promise<boolean>} Returns true on success
     * @throws {IntricError}
     * */
    delete: async (user) => {
      const { id } = user;
      await client.fetch("/api/v1/users/admin/{id}/", {
        method: "delete",
        params: { path: { id } }
      });
      return true;
    },

    /**
     * Update an existing user. Requires super user privileges.
     * @typedef {import('../types/fetch').JSONRequestBody<"post", "/api/v1/admin/users/{username}/">} UserLegacyUpdate
     * @typedef {import('../types/fetch').JSONRequestBody<"patch", "/api/v1/users/admin/{id}/">} UserUpdate
     * @param {{user: {id: string, username?: never}, update: UserUpdate} | {user: {username: string, id?: never}, update: UserLegacyUpdate}} params
     * @returns {Promise<User>}
     * @throws {IntricError}
     * */
    update: async (params) => {
      if ("username" in params.user && params.user.username) {
        const username = params.user.username;
        // We can cast this as we are on the "username" path
        const update = /** @type {UserLegacyUpdate} */ (params.update);
        const res = await client.fetch("/api/v1/admin/users/{username}/", {
          method: "post",
          params: { path: { username } },
          requestBody: { "application/json": update }
        });
        return res;
      }

      if ("id" in params.user && params.user.id) {
        const id = params.user.id;
        // We can cast this as we are on the "username" path
        const update = /** @type {UserUpdate} */ (params.update);
        const res = await client.fetch("/api/v1/users/admin/{id}/", {
          method: "patch",
          params: { path: { id } },
          requestBody: { "application/json": update }
        });
        return res;
      }

      throw Error("Either username or id are required to edit user");
    }
  };
}
