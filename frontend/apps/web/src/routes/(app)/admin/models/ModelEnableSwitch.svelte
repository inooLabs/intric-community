<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import { invalidate } from "$app/navigation";
  import { getIntric } from "$lib/core/Intric";
  import type { CompletionModel, EmbeddingModel } from "@intric/intric-js";
  import { Input, Tooltip } from "@intric/ui";

  export let model: (CompletionModel | EmbeddingModel) & { is_locked?: boolean | null | undefined };

  export let modeltype: "completion" | "embedding";

  const intric = getIntric();

  async function updateCompletionModel(
    completionModel: { id: string },
    update: { is_org_enabled?: boolean; security_level_id?: string | null }
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
    update: { is_org_enabled?: boolean; security_level_id?: string | null }
  ) {
    try {
      await intric.models.update({ embeddingModel, update });
      invalidate("admin:models:load");
    } catch (e) {
      alert(e);
      console.error(e);
    }
  }

  async function updateModel({ next }: { next: boolean }) {
    const update = {
      is_org_enabled: next ?? false,
      security_level_id: model.security_level_id
    };

    if (modeltype === "completion") {
      await updateCompletionModel({ id: model.id }, update);
    } else if (modeltype === "embedding") {
      await updateEmbeddingModel({ id: model.id }, update);
    } else {
      throw new Error("Invalid model type");
    }
  }

  $: tooltip = model.is_locked
    ? "EU-hosted models are available on request"
    : model.is_org_enabled
      ? "Toggle to disable model"
      : "Toggle to enable model";
</script>

<div class="-ml-3 flex items-center gap-4">
  <Tooltip text={tooltip}>
    <Input.Switch
      sideEffect={updateModel}
      value={model.is_org_enabled}
      disabled={model.is_locked}
    />
  </Tooltip>
</div>
