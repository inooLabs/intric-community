<script lang="ts">
    import { Button, Table } from "@intric/ui";
    import { createRender } from "svelte-headless-table";
    import type { SecurityLevel } from "@intric/intric-js";
    import SecurityLevelsTableRowActions from "./SecurityLevelsTableRowActions.svelte";

    export let securityLevels: SecurityLevel[] = [];

    const table = Table.createWithResource(securityLevels);

    const viewModel = table.createViewModel([
        table.column({ accessor: "name", header: "Name" }),
        table.column({ accessor: "value", header: "Value" }),
        table.column({ accessor: "description", header: "Description" }),
        table.columnActions({ cell: (row) => {
          return createRender(SecurityLevelsTableRowActions, {
            securityLevel: row.value
          });
        }
        }),
    ]);

    $: table.update(securityLevels);
</script>

<Table.Root {viewModel} resourceName="security-level" displayAs="list">
  <Table.Group />
</Table.Root>
