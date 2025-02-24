import type { PageLoad } from './$types';

export const load: PageLoad = async (event) => {
  const { intric } = await event.parent();
  event.depends("admin:security-levels:load");
  const securityLevels = await intric.securityLevels.getSecurityLevels();
  return {
    securityLevels
  };
};
