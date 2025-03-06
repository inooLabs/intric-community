<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import type { EmbeddingModel, SecurityLevel } from "@intric/intric-js";
  import { Table } from "@intric/ui";
  import { createRender } from "svelte-headless-table";
  import ModelEnableSwitch from "./ModelEnableSwitch.svelte";
  import ModelSecurityLevelSelect from "./ModelSecurityLevelSelect.svelte";
  import ModelTile from "./ModelTile.svelte";
  import {
    default as ModelLabels,
    getLabels
  } from "$lib/features/ai-models/components/ModelLabels.svelte";
  import { modelOrgs } from "$lib/features/ai-models/components/ModelNameAndVendor.svelte";
  import ModelCardDialog from "$lib/features/ai-models/components/ModelCardDialog.svelte";
  import ModelActions from "./ModelActions.svelte";

  export let embeddingModels: EmbeddingModel[];
  export let securityLevels: SecurityLevel[];

  const table = Table.createWithResource(embeddingModels);

  const viewModel = table.createViewModel([
    table.column({
      accessor: (model) => model,
      header: "Name",
      cell: (item) => {
        return createRender(ModelCardDialog, { model: item.value, includeTrigger: true });
      },
      plugins: {
        sort: {
          getSortValue(value) {
            return value.nickname;
          }
        },
        tableFilter: {
          getFilterValue(value) {
            return `${value.nickname} ${value.org}`;
          }
        }
      }
    }),
    table.column({
      accessor: (model) => model,
      header: "Enabled",
      cell: (item) => {
        return createRender(ModelEnableSwitch, { model: item.value, modeltype: "embedding" });
      },
      plugins: {
        sort: {
          getSortValue(value) {
            return value.can_access ? 1 : 0;
          }
        }
      }
    }),
    table.column({
      accessor: (model) => model,
      header: "Security Level",
      cell: (item) =>
        createRender(ModelSecurityLevelSelect, {
          model: item.value,
          modeltype: "embedding",
          securityLevels
        })
    }),
    table.column({
      accessor: (model) => model,
      header: "Labels",
      cell: (item) => createRender(ModelLabels, { model: item.value }),
      plugins: {
        sort: {
          disable: true
        },
        tableFilter: {
          getFilterValue(value) {
            const labels = getLabels(value).flatMap((label) => {
              return label.label;
            });
            return labels.join(" ");
          }
        }
      }
    }),

    table.columnActions({
      cell: (item) => {
        return createRender(ModelActions, { model: item.value });
      }
    }),
    table.columnCard({
      value: (item) => item.name,
      cell: (item) =>
        createRender(ModelTile, {
          model: item.value,
          modeltype: "embedding",
          securityLevels
        })
    })
  ]);

  function createOrgFilter(org: string | undefined | null) {
    return function (model: EmbeddingModel) {
      return model.org === org;
    };
  }

  $: table.update(embeddingModels);
</script>

<Table.Root {viewModel} resourceName="model" displayAs="list">
  {#each Object.entries(modelOrgs) as [org]}
    <Table.Group filterFn={createOrgFilter(org)} title={org} />
  {/each}
</Table.Root>
