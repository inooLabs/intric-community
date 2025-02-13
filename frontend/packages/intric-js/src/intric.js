import { createClient } from "./client/client";
import { initAnalytics } from "./endpoints/analysis";
import { initAssistants } from "./endpoints/assistants";
import { initDashboard } from "./endpoints/dashboard";
import { initFiles } from "./endpoints/files";
import { initGroups } from "./endpoints/groups";
import { initInfoBlobs } from "./endpoints/info-blobs";
import { initJobs } from "./endpoints/jobs";
import { initLimits } from "./endpoints/limits";
import { initLogging } from "./endpoints/logging";
import { initModels } from "./endpoints/models";
import { initRoles } from "./endpoints/roles";
import { initServices } from "./endpoints/services";
import { initSpaces } from "./endpoints/spaces";
import { initUserGroups } from "./endpoints/user-groups";
import { initUser } from "./endpoints/users";
import { initVersion } from "./endpoints/version";
import { initWebsites } from "./endpoints/websites";
import { initWidgets } from "./endpoints/widgets";
import { initPrompts } from "./endpoints/prompts";
import { initApps } from "./endpoints/apps";
import { initTemplates } from "./endpoints/templates";
import { initStorage } from "./endpoints/storage";

/**
 * Create an Intric.js object to interact with the intric backend.
 * Requires either an api key or a user token to authenticate requests.
 * @param {Object} args
 * @param  {string} [args.apiKey] Intric API key
 * @param  {string} [args.token] Intric auth token obtained through logging in
 * @param  {string} args.baseUrl Base URL of the Intric backend
 * @param {(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>} [args.fetch] Alternative fetch function to use, defaults to native fetch
 */
export function createIntric(args) {
  const client = createClient(args);
  return {
    apps: initApps(client),
    groups: initGroups(client),
    users: initUser(client),
    userGroups: initUserGroups(client),
    infoBlobs: initInfoBlobs(client),
    assistants: initAssistants(client),
    services: initServices(client),
    version: initVersion(client),
    analytics: initAnalytics(client),
    logging: initLogging(client),
    jobs: initJobs(client),
    widgets: initWidgets(client),
    roles: initRoles(client),
    files: initFiles(client),
    models: initModels(client),
    limits: initLimits(client),
    websites: initWebsites(client),
    spaces: initSpaces(client),
    dashboard: initDashboard(client),
    prompts: initPrompts(client),
    templates: initTemplates(client),
    storage: initStorage(client),
    client
  };
}
