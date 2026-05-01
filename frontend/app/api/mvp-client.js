import { buildQuestionPayload, buildStrategyPayload } from "../contracts/strategy-form.js";

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function loadBootstrapPayload() {
  return requestJson("/api/mvp/bootstrap");
}

export async function loadStrategyPayload(formValues) {
  return requestJson("/api/mvp/strategy", {
    method: "POST",
    body: JSON.stringify(buildStrategyPayload(formValues)),
  });
}

export async function askStrategyQuestion(formValues, question) {
  return requestJson("/api/mvp/question", {
    method: "POST",
    body: JSON.stringify(buildQuestionPayload(formValues, question)),
  });
}
