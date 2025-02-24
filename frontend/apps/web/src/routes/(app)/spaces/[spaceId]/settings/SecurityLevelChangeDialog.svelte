<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import type { SecurityLevel, SpaceUpdateDryRunResponse } from "@intric/intric-js";
  import { Dialog } from "@intric/ui";

  export let isOpen: Dialog.OpenState;
  export let currentSecurityLevel: SecurityLevel | undefined;
  export let newSecurityLevel: SecurityLevel | undefined;
  export let dryRunResult: SpaceUpdateDryRunResponse | undefined;
  export let onConfirm: () => void;
  export let onCancel: () => void;
</script>

<Dialog.Root alert bind:isOpen>
  <Dialog.Content>
    <Dialog.Title>Change Security Level</Dialog.Title>
    <Dialog.Description hidden>Change the security level of the space</Dialog.Description>

    <Dialog.Section>
      {#if dryRunResult?.unavailable_completion_models?.length || dryRunResult?.unavailable_embedding_models?.length}
        <div class="rounded-md border border-amber-200 bg-amber-50 p-4">
          <div class="flex items-start">
            <svg class="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
            </svg>
            <div class="ml-3">
              <h4 class="text-sm font-medium text-amber-800">Security Level Change</h4>
              <div class="mt-2 text-sm text-amber-700">
                <p class="mb-3">
                  You are about to change the security level from
                  <span class="font-medium">{currentSecurityLevel?.name || "None"}</span>
                  to
                  <span class="font-medium">{newSecurityLevel?.name || "None"}</span>.
                </p>
                {#if dryRunResult?.unavailable_completion_models?.length || dryRunResult?.unavailable_embedding_models?.length}
                  <p class="mb-3">Some models do not meet the new security level requirements and will be disabled.</p>
                {/if}
                {#if dryRunResult?.unavailable_completion_models?.length}
                  <div class="ml-1">
                    <p class="mb-1">Completion models:</p>
                    <ul class="list-disc space-y-1 pl-5">
                      {#each dryRunResult.unavailable_completion_models as model}
                        <li class="font-medium">{model.org}: {model.name}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
                {#if dryRunResult?.unavailable_embedding_models?.length}
                  <div class="mt-2 ml-1">
                    <p class="mb-1">Embedding models:</p>
                    <ul class="list-disc space-y-1 pl-5">
                      {#each dryRunResult.unavailable_embedding_models as model}
                        <li class="font-medium">{model.org}: {model.name}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {:else}
        <div class="rounded-md border border-blue-200 bg-blue-50 p-4">
          <div class="flex items-start">
            <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd" />
            </svg>
            <div class="ml-3">
              <h4 class="text-sm font-medium text-blue-800">Security Level Change</h4>
              <div class="mt-2 text-sm text-blue-700">
                <p>
                  You are about to change the security level from
                  <span class="font-medium">{currentSecurityLevel?.name || "None"}</span>
                  to
                  <span class="font-medium">{newSecurityLevel?.name || "None"}</span>.
                </p>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </Dialog.Section>

    <Dialog.Controls let:close>
      <button
        type="button"
        class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
        on:click={onCancel}
      >
        Cancel
      </button>
      <button
        type="button"
        class="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        on:click={onConfirm}
      >
        Confirm Change
      </button>
    </Dialog.Controls>
  </Dialog.Content>
</Dialog.Root>
