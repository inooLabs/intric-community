/*
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
*/

export const load = async (event) => {
  const { intric } = await event.parent();

  const models = await intric.models.list();
  const securityLevels = await intric.securityLevels.getSecurityLevels();

  return {
    ...models,
    securityLevels
  };
};
