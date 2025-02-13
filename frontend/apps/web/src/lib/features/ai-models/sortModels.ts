import type { CompletionModel, EmbeddingModel } from "@intric/intric-js";

type Model = (CompletionModel | EmbeddingModel) & { nickname?: string | null };

function sortModel(a: Model, b: Model) {
  if (a.org === b.org) {
    return (a.nickname ?? "a") > (b.nickname ?? "b") ? 1 : -1;
  }
  return (a.org ?? "a") > (b.org ?? "b") ? 1 : -1;
}

/** Will sort an array of `CompletionModel`or `EmbeddingModel`. ATTENTION: sorts in place! */
export function sortModels(models: Model[]) {
  models.sort(sortModel);
  return models;
}
