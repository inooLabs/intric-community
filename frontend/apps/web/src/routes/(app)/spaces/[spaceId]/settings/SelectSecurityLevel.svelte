<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import { getSpacesManager } from "$lib/features/spaces/SpacesManager";
  import type { CompletionModel, EmbeddingModel, SecurityLevel, SpaceUpdateDryRunResponse } from "@intric/intric-js";
  import { Dialog } from "@intric/ui";
  import SecurityLevelChangeDialog from "./SecurityLevelChangeDialog.svelte";

  export let securityLevels: SecurityLevel[];
  export let embeddingModels: EmbeddingModel[];
  export let completionModels: CompletionModel[];

  const {
    state: { currentSpace },
    updateSpace,
    refreshCurrentSpace,
    updateSpaceDryrun
  } = getSpacesManager();

  let securityLevel: SecurityLevel | undefined;
  $: if (securityLevels) {
    securityLevel = securityLevels.find(level => level.id === $currentSpace.security_level?.id);
  }

  let isUpdating = false;
  let showConfirmDialog: Dialog.OpenState;
  let pendingSecurityLevel: SecurityLevel | undefined;
  let dryRunResult: SpaceUpdateDryRunResponse | undefined;

  // Prepare options for RadioGroup
  $: radioOptions = [
    { value: undefined, label: "No security level" },
    ...securityLevels.map(level => ({ value: level, label: level.name }))
  ];

  async function updateSecurityLevel(levelId: string | null) {
    try {
      isUpdating = true;
      await updateSpace({ security_level_id: levelId });
      await refreshCurrentSpace();
    } catch (e) {
      console.error("Error updating security level", e);
      alert("Failed to update security level");
    } finally {
      isUpdating = false;
    }
  }

  async function handleSecurityLevelChange(level: SecurityLevel | undefined) {
    if (isUpdating || level === securityLevel) return;

    pendingSecurityLevel = level;
    try {
      dryRunResult = await updateSpaceDryrun({
        security_level_id: level?.id ?? null
      });
      $showConfirmDialog = true;
    } catch (error) {
      console.error("Error running security level change dry run:", error);
      alert("Failed to check security level change implications");
    }
  }

  function handleConfirmChange() {
    $showConfirmDialog = false;
    updateSecurityLevel(pendingSecurityLevel?.id ?? null);
    securityLevel = pendingSecurityLevel;
  }

  function handleCancelChange() {
    $showConfirmDialog = false;
    pendingSecurityLevel = securityLevel;
  }

  function hasModelWithIncompatibleSecurityLevel<T extends { id: string }>(
    spaceModels: Array<T>,
    allModels: Array<{ id: string; security_level_id?: string | null }>,
    currentSecurityLevel: SecurityLevel
  ): boolean {
    return spaceModels.some(spaceModel => {
      const model = allModels.find(m => m.id === spaceModel.id);
      if (!model) return false;
      const modelSecurityLevel = securityLevels.find(level => level.id === model.security_level_id)?.value ?? 0;
      return modelSecurityLevel < currentSecurityLevel.value;
    });
  }

  function hasIncompatibleModels(currentSecurityLevel: SecurityLevel): boolean {
    if (!currentSecurityLevel) return false;

    return (
      hasModelWithIncompatibleSecurityLevel($currentSpace.completion_models, completionModels, currentSecurityLevel) ||
      hasModelWithIncompatibleSecurityLevel($currentSpace.embedding_models, embeddingModels, currentSecurityLevel)
    );
  }
</script>

<SecurityLevelChangeDialog
  bind:isOpen={showConfirmDialog}
  currentSecurityLevel={securityLevel}
  newSecurityLevel={pendingSecurityLevel}
  {dryRunResult}
  onConfirm={handleConfirmChange}
  onCancel={handleCancelChange}
/>

<div class="flex flex-col gap-4 py-5 pr-6 lg:flex-row lg:gap-12">
  <div class="pl-2 pr-12 lg:w-2/5">
    <h3 class="pb-1 text-lg font-medium">Security Level</h3>
    <p class="text-secondary">Set the security level for this space and all its resources.</p>
    {#if securityLevel && hasIncompatibleModels(securityLevel)}
      <p class="mt-2.5 rounded-md border border-warning-default bg-warning-dimmer px-2 py-1 text-sm text-warning-stronger">
        <span class="font-bold">Warning:&nbsp;</span>Some AI models don't meet the selected security level and will be unavailable.
      </p>
    {/if}
  </div>
  <div class="flex-grow min-w-0 w-full lg:pl-12 lg:max-w-[60%]">
    <div class="overflow-hidden rounded-lg border border-default bg-primary shadow">
      <div class="cursor-pointer border-b border-default last:border-b-0">
        <div class="px-4 py-3 font-medium">Security level</div>
        <div class="flex flex-col">
          {#each radioOptions as option}
            <label class="flex cursor-pointer flex-col border-t border-default px-4 py-3 hover:bg-hover-dimmer">
              <div class="flex items-center gap-3">
                <input
                  type="radio"
                  name="security-level"
                  class="h-4 w-4 cursor-pointer text-accent-default"
                  checked={option.value === (pendingSecurityLevel ?? securityLevel)}
                  disabled={isUpdating}
                  on:change={() => handleSecurityLevelChange(option.value)}
                />
                <span class="font-medium">{option.label}</span>
              </div>
              {#if option.value?.description}
                <p class="mt-1 ml-7 text-sm text-secondary break-words">{option.value.description}</p>
              {:else if !option.value}
                <p class="mt-1 ml-7 text-sm text-secondary break-words">No specific security requirements for this space.</p>
              {/if}
            </label>
          {/each}
        </div>
      </div>
    </div>
  </div>
</div>
