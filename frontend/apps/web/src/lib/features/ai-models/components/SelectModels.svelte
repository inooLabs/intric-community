<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import { getSpacesManager } from "$lib/features/spaces/SpacesManager";
  import type { CompletionModel, EmbeddingModel, SecurityLevel } from "@intric/intric-js";
  import ModelNameAndVendor from "./ModelNameAndVendor.svelte";
  import { Input } from "@intric/ui";
  import { derived } from "svelte/store";

  type Model = CompletionModel | EmbeddingModel;
  type ModelType = "completion" | "embedding";

  export let selectableModels: Model[];
  export let securityLevels: SecurityLevel[];
  export let modelType: ModelType;
  export let title: string;
  export let description: string;

  selectableModels.sort(sortModel);

  function sortModel(a: Model, b: Model) {
    if (a.org === b.org) {
      const aName = modelType === "embedding" ? (a as EmbeddingModel).name : (a as CompletionModel).nickname;
      const bName = modelType === "embedding" ? (b as EmbeddingModel).name : (b as CompletionModel).nickname;
      return (aName ?? "a") > (bName ?? "b") ? 1 : -1;
    }
    return (a.org ?? "a") > (b.org ?? "b") ? 1 : -1;
  }

  const {
    state: { currentSpace },
    updateSpace
  } = getSpacesManager();

  function modelHasHighEnoughSecurityLevel(model: Model) {
    const spaceSecurityLevel = $currentSpace.security_level?.value ?? 0;
    if (!spaceSecurityLevel) return true;

    const modelSecurityLevel = securityLevels.find((level) => level.id === model.security_level_id)?.value ?? 0;
    return modelSecurityLevel >= spaceSecurityLevel;
  }

  function getAvailableModels() {
    return selectableModels.filter((model) => modelHasHighEnoughSecurityLevel(model));
  }

  $: availableModels = getAvailableModels();

  $: {
    // This block will re-run whenever $currentSpace changes
    $currentSpace;
    availableModels = getAvailableModels();
  }

  const currentlySelectedModels = derived(
    currentSpace,
    ($currentSpace) => modelType === "embedding"
      ? $currentSpace.embedding_models.map((model) => model.id) ?? []
      : $currentSpace.completion_models.map((model) => model.id) ?? []
  );

  let loading = new Set<string>();
  async function toggleModel(model: Model) {
    loading.add(model.id);
    loading = loading;

    try {
      const newModels = $currentlySelectedModels.includes(model.id)
        ? $currentlySelectedModels.filter((id) => id !== model.id)
        : [...$currentlySelectedModels, model.id];

      const updateData = {
        [modelType === "embedding" ? "embedding_models" : "completion_models"]: newModels.map((id) => ({ id })),
        security_level_id: $currentSpace.security_level?.id
      };

      await updateSpace(updateData);
    } catch (e) {
      alert(e);
    }
    loading.delete(model.id);
    loading = loading;
  }
</script>

<div class="flex flex-col gap-4 pb-2 lg:flex-row lg:gap-12">
  <div class="pl-2 pr-12 lg:w-2/5">
    <h3 class="pb-1 text-lg font-medium">{title}</h3>
    <p class="text-stone-500">
      {description}
    </p>
    {#if $currentlySelectedModels.length === 0}
      <p
        class="mt-2.5 rounded-md border border-amber-500 bg-amber-50 px-2 py-1 text-sm text-amber-800"
      >
        <span class="font-bold">Hint:&nbsp;</span>
        {#if modelType === "embedding"}
          Enable an embedding model to be able to use knowledge from collections and websites.
        {:else}
          Enable at least one completion model to be able to use assistants.
        {/if}
      </p>
    {:else if modelType === "embedding" && $currentlySelectedModels.length > 1}
      <p
        class="mt-2.5 rounded-md border border-amber-500 bg-amber-50 px-2 py-1 text-sm text-amber-800"
      >
        <span class="font-bold">Hint:&nbsp;</span>We strongly recommend to only activate one
        embedding model per space. Data embedded with different models is not compatible with each
        other.
      </p>
    {/if}
  </div>

  <div class="flex flex-grow flex-col">
    {#if availableModels.length === 0}
      <p class="mt-2.5 rounded-md border border-amber-500 bg-amber-50 px-2 py-1 text-sm text-amber-800">
        No models available that match this space's security level <span class="font-bold">{ $currentSpace.security_level?.name }</span>.
      </p>
    {:else}
      {#each availableModels as model (model.id)}
        <div
          class="cursor-pointer border-b py-4 pl-2 pr-4 transition-colors hover:[background:var(--background-hover-dimmer)] [border-color:var(--border-default)]"
        >
          <Input.Switch
            value={$currentlySelectedModels.includes(model.id)}
            sideEffect={() => toggleModel(model)}
          >
            <ModelNameAndVendor {model} />
          </Input.Switch>
        </div>
      {/each}
    {/if}
  </div>
</div>
