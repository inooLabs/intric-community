/*
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
*/

import { createAsyncState } from "$lib/core/helpers/createAsyncState.svelte";
import { createClassContext } from "$lib/core/helpers/createClassContext";
import { type SecurityClassification, type Intric } from "@intric/intric-js";

class SecurityClassificationsService {
  #intric: Intric;
  #enabled = $state(false);
  isSecurityEnabled = $derived(this.#enabled);

  #classifications = $state<SecurityClassification[]>([]);
  classifications = $derived.by(() => this.#classifications.toReversed());

  constructor(
    intric: Intric,
    securityClassifications?: {
      security_enabled: boolean;
      security_classifications: SecurityClassification[];
    }
  ) {
    this.#intric = intric;
    if (securityClassifications) {
      this.#enabled = securityClassifications.security_enabled;
      this.#classifications = securityClassifications.security_classifications;
    }
  }

  enable = createAsyncState(async () => {
    const isEnabled = await this.#intric.securityClassifications
      .enable()
      .then((res) => res.security_enabled);
    this.#enabled = isEnabled;
    return isEnabled;
  });

  disable = createAsyncState(async () => {
    const isEnabled = await this.#intric.securityClassifications
      .disable()
      .then((res) => res.security_enabled);
    this.#enabled = isEnabled;
    return isEnabled;
  });

  async createClassification(classification: { name: string; description: string }) {
    const res = await this.#intric.securityClassifications.create({
      ...classification,
      insertAs: "lowest"
    });
    this.#classifications.unshift(res);
  }

  async deleteClassification(classification: { id: string }) {
    await this.#intric.securityClassifications.delete(classification);
    const idx = this.#classifications.findIndex(({ id }) => id === classification.id);
    this.#classifications.splice(idx, 1);
  }

  async updateClassification(classification: { id: string; name?: string; description?: string }) {
    const updated = await this.#intric.securityClassifications.update(classification);
    const idx = this.#classifications.findIndex(({ id }) => id === classification.id);
    this.#classifications[idx] = updated;
  }

  async move(classification: { id: string }, direction: "up" | "down") {
    const reordered = this.#classifications.map(({ id, name, description }) => {
      return { id, name, description };
    });
    const idx = reordered.findIndex(({ id }) => id === classification.id);
    const move = reordered[idx];

    if (direction === "up") {
      if (idx < 0 || idx >= reordered.length - 1) return;
      reordered[idx] = reordered[idx + 1];
      reordered[idx + 1] = move;
    } else {
      if (idx <= 0) return;
      reordered[idx] = reordered[idx - 1];
      reordered[idx - 1] = move;
    }

    this.#classifications = await this.#intric.securityClassifications.rank(reordered);
  }
}

export const [getSecurityClassificationService, initSecurityClassificationService] =
  createClassContext("security classifications", SecurityClassificationsService);
