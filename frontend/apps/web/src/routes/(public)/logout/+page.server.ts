import { redirect } from "@sveltejs/kit";
import {
  clearFrontendCookies,
  decodeState,
  encodeState,
  type LogoutStateParam
} from "$lib/features/auth/auth.server";
import { env } from "$env/dynamic/private";

export const load = async (event) => {
  // always delete cookies
  clearFrontendCookies(event);

  // Message to show, we just pass this on
  const message = event.url.searchParams.get("message") ?? undefined;

  // Feature flag should guarantee ZITADEL_PROJECT_CLIENT_ID and ZITADEL_INSTANCE_URL to be set
  if (event.locals.featureFlags.newAuth) {
    const state = decodeState<LogoutStateParam>(event.url.searchParams.get("state"));

    // If we are coming back from Zitadel (state.completed === true),
    // We return and the +page.svelte will be rendered with the message like a normal page load
    if (state && state.completed) {
      return {
        message: state.message ?? "logout"
      };
    }

    // Otherwise we first redirect to Zitadel for logout and wait until we come back from there
    const searchParams = new URLSearchParams({
      client_id: env.ZITADEL_PROJECT_CLIENT_ID!,
      post_logout_redirect_uri: `${event.url.origin}/logout`,
      state: encodeState({
        completed: true,
        message
      })
    });

    if (event.locals.id_token) {
      searchParams.append("id_token_hint", event.locals.id_token);
    }

    const redirectUrl =
      env.ZITADEL_INSTANCE_URL! + "/oidc/v1/end_session?" + searchParams.toString();

    redirect(302, redirectUrl);
  }

  // Fallback for old auth
  redirect(302, `/login?message=${message ?? "logout"}`);
};
