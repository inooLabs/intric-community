/*
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
*/

export const load = async (event) => {
  const { intric } = await event.parent();

  event.depends("admin:models:load");

  const securityLevels = await intric.securityLevels.getSecurityLevels();
  const models = await intric.models.list();

  return {
    models,
    securityLevels
  };
};
