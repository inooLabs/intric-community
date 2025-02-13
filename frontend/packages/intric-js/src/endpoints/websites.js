/** @typedef {import('../client/client').IntricError} IntricError */
/** @typedef {import('../types/resources').Website} Website */
/** @typedef {import('../types/resources').CrawlRun} CrawlRun */
/** @typedef {import('../types/resources').EmbeddingModel} EmbeddingModel  */

/**
 * @param {import('../client/client').Client} client Provide a client with which to call the endpoints
 */
export function initWebsites(client) {
  return {
    /**
     * Lists all configured websites on this tenant.
     * @param {{includeTenant?: boolean} | undefined} [options]  Include all websites of this tenant?
     * @returns {Promise<Website[]>}
     * @throws {IntricError}
     * */
    list: async (options) => {
      const res = await client.fetch("/api/v1/websites/", {
        method: "get",
        params: {
          query: {
            for_tenant: options?.includeTenant
          }
        }
      });
      return res.items;
    },

    /**
     * Creates a new website for the current tenant.
     * @param {Omit<import('../types/fetch').JSONRequestBody<"post", "/api/v1/websites/">, "space_id"> & {spaceId?: string}} website
     * @returns {Promise<Website>} Returns the created website
     * @throws {IntricError}
     */
    create: async (website) => {
      if ("spaceId" in website && website.spaceId) {
        const res = await client.fetch("/api/v1/spaces/{id}/knowledge/websites/", {
          method: "post",
          params: {
            path: {
              id: website.spaceId
            }
          },
          requestBody: {
            "application/json": website
          }
        });
        return res;
      }

      const res = await client.fetch("/api/v1/websites/", {
        method: "post",
        requestBody: {
          "application/json": website
        }
      });
      return res;
    },

    /**
     * Transfer a website into a different space. Needs matching embedding model to be available.
     * Throws error on failure
     * @param {{website: {id: string}, targetSpace: {id: string}}} params
     * @throws {IntricError}
     * */
    transfer: async ({ website, targetSpace }) => {
      const { id } = website;
      await client.fetch("/api/v1/websites/{id}/transfer/", {
        method: "post",
        params: { path: { id } },
        requestBody: {
          "application/json": {
            target_space_id: targetSpace.id
          }
        }
      });
      return true;
    },

    /**
     * Get a website by its id.
     * @param {{id: string} | Website} website Website to get
     * @returns {Promise<Website>}
     * @throws {IntricError}
     * */
    get: async (website) => {
      const { id } = website;
      const res = await client.fetch("/api/v1/websites/{id}/", {
        method: "get",
        params: { path: { id } }
      });
      return res;
    },

    /**
     * Delete a website by its id.
     * @param {{id: string} | Website} website Website to delete
     * @returns {Promise<Website>} Returns deleted website
     * @throws {IntricError}
     * */
    delete: async (website) => {
      const { id } = website;
      const res = await client.fetch("/api/v1/websites/{id}/", {
        method: "delete",
        params: { path: { id } }
      });
      return res;
    },

    /**
     * Update an existing website.
     * @param {Object} params
     * @param {{id: string} | Website} params.website Website to update
     * @param {import('../types/fetch').JSONRequestBody<"post", "/api/v1/websites/{id}/">} params.update Supply properties to update.
     * @returns {Promise<Website>} Returns the updated website.
     * @throws {IntricError}
     * */
    update: async ({ website, update }) => {
      const { id } = website;
      const res = await client.fetch("/api/v1/websites/{id}/", {
        method: "post",
        params: { path: { id } },
        requestBody: { "application/json": update }
      });
      return res;
    },

    indexedBlobs: {
      /**
       * List all info-blobs (=> crawl results) of a specific website
       * @param {{id: string} | Website} website Website
       * @returns {Promise<import('./files').InfoBlob[]>}
       * @throws {IntricError}
       * */
      list: async (website) => {
        const { id } = website;
        const res = await client.fetch("/api/v1/websites/{id}/info-blobs/", {
          method: "get",
          params: { path: { id } }
        });
        return res.items;
      }
    },

    crawlRuns: {
      /**
       * List all runs of a specific website
       * @param {{id: string} | Website} website Website
       * @returns {Promise<CrawlRun[]>}
       * @throws {IntricError}
       * */
      list: async (website) => {
        const { id } = website;
        const res = await client.fetch("/api/v1/websites/{id}/runs/", {
          method: "get",
          params: { path: { id } }
        });
        return res.items;
      },

      /**
       * Manually trigger a new crawl run
       * @param {{id: string} | Website} website Website
       * @returns {Promise<CrawlRun>}
       * @throws {IntricError}
       * */
      create: async (website) => {
        const { id } = website;
        const res = await client.fetch("/api/v1/websites/{id}/run/", {
          method: "post",
          params: { path: { id } }
        });
        return res;
      }
    }
  };
}
