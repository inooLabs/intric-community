<script lang="ts">
  import { invalidate } from "$app/navigation";
  import { getIntric } from "$lib/core/Intric";
  import { Button, Dialog, Input } from "@intric/ui";
  import type { SecurityLevel } from "@intric/intric-js";
  import { onMount } from "svelte";

  const intric = getIntric();

  export let securityLevel: SecurityLevel | undefined = undefined;
  export let onComplete = () => {};

  let newSecurityLevelName = "";
  let newSecurityLevelDescription = "";
  let newSecurityLevelValue = 0;
  let isProcessing = false;
  let showDialog: Dialog.OpenState;

  function initializeFields() {
    if (securityLevel) {
      newSecurityLevelName = securityLevel.name;
      newSecurityLevelDescription = securityLevel.description ?? "";
      newSecurityLevelValue = securityLevel.value;
    } else {
      newSecurityLevelName = "";
      newSecurityLevelDescription = "";
      newSecurityLevelValue = 0;
    }
  }

  // Initialize fields when securityLevel changes
  $: if ($showDialog) {
    initializeFields();
  }

  onMount(() => {
    initializeFields();
  });

  async function handleSubmit() {
    if (newSecurityLevelName === "") return;
    isProcessing = true;

    try {
      if (securityLevel) {
        await intric.securityLevels.updateSecurityLevel(securityLevel.id, {
          name: newSecurityLevelName,
          description: newSecurityLevelDescription,
          value: newSecurityLevelValue
        });
      } else {
        await intric.securityLevels.createSecurityLevel({
          name: newSecurityLevelName,
          description: newSecurityLevelDescription,
          value: newSecurityLevelValue
        });
      }

      invalidate("admin:security-levels:load");
      $showDialog = false;
      newSecurityLevelName = "";
      newSecurityLevelDescription = "";
      newSecurityLevelValue = 0;
      onComplete();
    } catch (e) {
      alert(`Error ${securityLevel ? "updating" : "creating"} security level`);
      console.error(e);
    }
    isProcessing = false;
  }
</script>

<Dialog.Root alert bind:isOpen={showDialog}>
  <Dialog.Trigger asFragment let:trigger>
    <slot {trigger}>
      <Button is={trigger} variant={securityLevel ? "primary-outlined" : "primary"}>{securityLevel ? "Edit" : "Create security level"}</Button>
    </slot>
  </Dialog.Trigger>
  <Dialog.Content wide form>
    <Dialog.Title>{securityLevel ? "Edit" : "Create"} security level</Dialog.Title>

    <Dialog.Section>
      <Input.Text
        bind:value={newSecurityLevelName}
        required
        class="border-b border-stone-100 px-4 py-4 hover:bg-stone-50">Name</Input.Text>
      <Input.Text bind:value={newSecurityLevelDescription} required class="border-b border-stone-100 px-4 py-4 hover:bg-stone-50">Description</Input.Text>
      <Input.Number bind:value={newSecurityLevelValue} required class="border-b border-stone-100 px-4 py-4 hover:bg-stone-50">Value</Input.Number>
    </Dialog.Section>

    <Dialog.Controls let:close>
      <Button is={close}>Cancel</Button>
      <Button
        variant="primary"
        on:click={handleSubmit}
        disabled={isProcessing}
        >{isProcessing ? (securityLevel ? "Updating..." : "Creating...") : (securityLevel ? "Update security level" : "Create security level")}</Button
      >
    </Dialog.Controls>
  </Dialog.Content>
</Dialog.Root>
