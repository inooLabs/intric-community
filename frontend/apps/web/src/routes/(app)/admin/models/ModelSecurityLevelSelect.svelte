<!--
    Copyright (c) 2025 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import type { SecurityLevel } from "@intric/intric-js";
  import { invalidate } from "$app/navigation";
  import { getIntric } from "$lib/core/Intric";
  import { Select } from "@intric/ui";
  import { writable, type Writable } from "svelte/store";
  import type { SelectOption } from "@melt-ui/svelte";

  export let model: {
    id: string;
    is_locked?: boolean;
    security_level_id?: string | null;
    is_org_enabled?: boolean;
  };
  export let modeltype: "completion" | "embedding";
  export let securityLevels: SecurityLevel[];

  let securityLevel: SecurityLevel | undefined;

  $: if (securityLevels) {
    securityLevel = securityLevels.find((level) => level.id === model.security_level_id);
  }

  const intric = getIntric();

  async function updateCompletionModel(
    completionModel: { id: string },
    update: { security_level_id?: string | null; is_org_enabled?: boolean }
  ) {
    try {
      await intric.models.update({ completionModel, update });
      invalidate("admin:models:load");
    } catch (e) {
      alert(e);
      console.error(e);
    }
  }

  async function updateEmbeddingModel(
    embeddingModel: { id: string },
    update: { security_level_id?: string | null; is_org_enabled?: boolean }
  ) {
    try {
      await intric.models.update({ embeddingModel, update });
      invalidate("admin:models:load");
    } catch (e) {
      alert(e);
      console.error(e);
    }
  }

  async function updateSecurityLevel(levelId: string | null) {
    if (model.is_locked) return;

    const update = {
      security_level_id: levelId || undefined,
      is_org_enabled: model.is_org_enabled ?? false
    };

    if (modeltype === "completion") {
      await updateCompletionModel({ id: model.id }, update);
    } else if (modeltype === "embedding") {
      await updateEmbeddingModel({ id: model.id }, update);
    } else {
      throw new Error("Invalid model type");
    }
  }

  $: options = [
    { value: null, label: "No security level" },
    ...securityLevels.map(level => ({
      value: level.id,
      label: level.name
    }))
  ];

  const selectedOption: Writable<SelectOption<string | null>> = writable({
    value: model.security_level_id ?? null,
    label: securityLevel?.name ?? "No security level"
  });

  $: {
    const currentOption = options.find(opt => opt.value === model.security_level_id);
    if (currentOption) {
      selectedOption.set(currentOption);
    }
  }

  $: if ($selectedOption?.value !== model.security_level_id) {
    updateSecurityLevel($selectedOption?.value ?? null);
  }
</script>

<div>
  {#if securityLevels.length === 0}
    <div class="text-stone-600 text-sm">No security level</div>
  {:else}
    <div class="-mb-1.5">
      <Select.Root customStore={selectedOption} disabled={model.is_locked} class="w-48">
        <Select.Trigger />
        <Select.Options>
          {#each options as option}
            <Select.Item value={option.value} label={option.label} />
          {/each}
        </Select.Options>
      </Select.Root>
    </div>
  {/if}
</div>
