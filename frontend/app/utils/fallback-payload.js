import { fallbackPayload as fallbackPayloadSeed } from "../stores/fallback-data.js";

export function buildFallbackPayload(localPlan, scope) {
  return {
    ...fallbackPayloadSeed,
    strategy: localPlan,
    results: {
      ...fallbackPayloadSeed.results,
      label: scope,
    },
  };
}

export { fallbackPayloadSeed };
