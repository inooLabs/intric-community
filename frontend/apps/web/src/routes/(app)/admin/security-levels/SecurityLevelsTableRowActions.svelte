<script lang="ts">
  import { Button, Dialog } from "@intric/ui";
  import type { SecurityLevel } from "@intric/intric-js";
  import { getIntric } from "$lib/core/Intric";
  import { invalidate } from "$app/navigation";
  import SecurityLevelDialog from "./SecurityLevelDialog.svelte";

  const intric = getIntric();

  export let securityLevel: SecurityLevel;

  let isDeleting = false;
  let showDeleteDialog: Dialog.OpenState;

  async function deleteSecurityLevel() {
    isDeleting = true;
    try {
      await intric.securityLevels.deleteSecurityLevel(securityLevel.id);
      invalidate("admin:security-levels:load");
      $showDeleteDialog = false;
    } catch (e) {
      alert("Could not delete security level.");
      console.error(e);
    }
    isDeleting = false;
  }
</script>

<div class="flex gap-2">
  <SecurityLevelDialog {securityLevel}></SecurityLevelDialog>

  <Dialog.Root alert bind:isOpen={showDeleteDialog}>
    <Dialog.Trigger asFragment let:trigger>
      <Button is={trigger} destructive label="Delete">
        <span>Delete</span>
      </Button>
    </Dialog.Trigger>

    <Dialog.Content>
      <Dialog.Title>Delete security level</Dialog.Title>
      <Dialog.Description>
        Do you really want to delete <span class="italic">{securityLevel.name}</span>?
      </Dialog.Description>

      <Dialog.Controls let:close>
        <Button is={close}>Cancel</Button>
        <Button disabled={isDeleting} destructive on:click={deleteSecurityLevel}>
          {isDeleting ? "Deleting..." : "Delete"}
        </Button>
      </Dialog.Controls>
    </Dialog.Content>
  </Dialog.Root>
</div>
