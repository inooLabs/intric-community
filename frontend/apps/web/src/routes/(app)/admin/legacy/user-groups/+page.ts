/*
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
*/

export const load = async (event) => {
  event.depends("admin:user-groups:load");

  const { intric } = await event.parent();
  const userGroups = await intric.userGroups.list();

  return {
    userGroups
  };
};
