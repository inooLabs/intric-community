<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import { Page } from "$lib/components/layout/index.js";
  import SecurityLevelsTable from "./SecurityLevelsTable.svelte";
  import SecurityLevelDialog from "./SecurityLevelDialog.svelte";
  export let data;

</script>

<svelte:head>
  <title>Intric.ai – Admin – Security Levels</title>
</svelte:head>


<Page.Root>
  <Page.Header>
    <Page.Title title="Security Levels"></Page.Title>
    <SecurityLevelDialog></SecurityLevelDialog>
  </Page.Header>
  <Page.Main>
    <SecurityLevelsTable securityLevels={data.securityLevels} />
  </Page.Main>
</Page.Root>
