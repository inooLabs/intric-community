<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import type { CompletionModel, EmbeddingModel, SecurityLevel } from "@intric/intric-js";
  import ModelEnableSwitch from "./ModelEnableSwitch.svelte";
  import ModelSecurityLevelSelect from "./ModelSecurityLevelSelect.svelte";
  import { Label } from "@intric/ui";
  import { getLabels } from "$lib/features/ai-models/components/ModelLabels.svelte";
  import ModelNameAndVendor from "$lib/features/ai-models/components/ModelNameAndVendor.svelte";

  export let model: CompletionModel | EmbeddingModel;
  export let modeltype: "completion" | "embedding";
  export let securityLevels: SecurityLevel[];

  let labels = getLabels(model);
</script>

<div
  class="flex w-[24rem] flex-col rounded-xl border border-b-2 border-default bg-secondary shadow"
>
  <div
    class="-m-[1px] flex flex-grow flex-col rounded-lg border border-default bg-primary shadow-sm"
  >
    <div class="flex flex-col gap-2 p-4">
      <ModelNameAndVendor {model} size="card"></ModelNameAndVendor>
      <div class="pt-2">
        {model.description}
      </div>
    </div>
    <div class="h-[1px] bg-hover-default"></div>
    <div class="flex flex-col items-start px-4 pb-3 pt-1">
      <Label.List
        content={[
          {
            label: model.name,
            color: "blue",
            tooltip: "Full model name"
          }
        ]}
        capitalize={false}
        monospaced={true}>Full name</Label.List
      >
      <Label.List content={labels}>Details</Label.List>
    </div>
  </div>
  <div>
    <div class="flex h-full flex-col gap-2 px-5 py-4">
      <div class="flex items-center justify-between">
        <p>Enabled</p>
        <ModelEnableSwitch {model} {modeltype} />
      </div>
      <div class="flex items-center justify-between">
        <p>Security Level</p>
        <ModelSecurityLevelSelect {model} {modeltype} {securityLevels} />
      </div>
    </div>
  </div>
</div>
