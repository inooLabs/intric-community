<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import type { CompletionModel, SecurityLevel } from "@intric/intric-js";
  import { Table } from "@intric/ui";
  import { createRender } from "svelte-headless-table";
  import ModelEnableSwitch from "./ModelEnableSwitch.svelte";
  import ModelTile from "./ModelTile.svelte";
  import ModelSecurityLevelSelect from "./ModelSecurityLevelSelect.svelte";
  import {
    default as ModelLabels,
    getLabels
  } from "$lib/features/ai-models/components/ModelLabels.svelte";
  import { modelOrgs } from "$lib/features/ai-models/components/ModelNameAndVendor.svelte";
  import ModelActions from "./ModelActions.svelte";
  import ModelCardDialog from "$lib/features/ai-models/components/ModelCardDialog.svelte";

  export let completionModels: CompletionModel[];
  export let securityLevels: SecurityLevel[];

  const table = Table.createWithResource(completionModels);

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
    table.column({ accessor: "name", header: "Model" }),
    table.column({
      accessor: (model) => model,
      header: "Enabled",
      cell: (item) =>
        createRender(ModelEnableSwitch, { model: item.value, modeltype: "completion" }),
      plugins: {
        sort: {
          getSortValue(value) {
            return value.is_org_enabled ? 1 : 0;
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
          modeltype: "completion",
          securityLevels
        })
    }),
    table.column({
      accessor: (model) => model,
      header: "Details",
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
    table.columnCard({
      value: (item) => item.name,
      cell: (item) =>
        createRender(ModelTile, {
          model: item.value,
          modeltype: "completion",
          securityLevels
        })
    })
  ]);

  function createOrgFilter(org: string | null | undefined) {
    return function (model: CompletionModel) {
      return model.org === org;
    };
  }

  $: table.update(completionModels);
</script>

<Table.Root {viewModel} resourceName="model" displayAs="list">
  {#each Object.entries(modelOrgs) as [org]}
    <Table.Group filterFn={createOrgFilter(org)} title={org} />
  {/each}
</Table.Root>
