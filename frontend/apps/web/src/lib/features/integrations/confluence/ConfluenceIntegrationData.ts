import type { IntegrationData } from "../IntegrationData";
import confluenceImgUrl from "./confluence.png";
import ConfluenceImportDialog from "./ConfluenceImportDialog.svelte";

export const ConfluenceIntegrationData: IntegrationData = {
  logo: confluenceImgUrl,
  description:
    "This integration enables the seamless import of knowledge from Confluence spaces into intric.",
  displayName: "Confluence",
  importHint: "Import a Confluence space into your knowledge",
  ImportDialog: ConfluenceImportDialog,
  previewLinkLabel: "Open in Confluence"
};
