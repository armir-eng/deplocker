import { RequestParams } from "./types";

const jsonPayloadHeader = {
  "Content-Type": "application/json",
};

export const parameterLessEndpoints: Record<string, RequestParams> = {
  [`${API_URL}/auth/register`]: {
    method: "POST",
    public: true,
    headers: {
      ...jsonPayloadHeader,
    },
  },
  [`${API_URL}/auth/login`]: {
    method: "POST",
  },
  [`${API_URL}/auth/passkeys/login/options`]: {
    method: "POST",
  },
  [`${API_URL}/auth/passkeys/login`]: {
    method: "POST",
    headers: {
      ...jsonPayloadHeader,
    },
  },
  [`${API_URL}/auth/passkeys/register/options`]: {
    method: "POST",
  },
  [`${API_URL}/auth/passkeys/register`]: {
    method: "POST",
    headers: {
      ...jsonPayloadHeader,
    },
  },
  [`${API_URL}/health`]: {
    method: "GET",
    public: true,
  },
  [`${API_URL}/auth/session/check`]: {
    method: "GET",
  },
  [`${API_URL}/projects/create`]: {
    method: "GET",
    headers: {
      ...jsonPayloadHeader,
    },
  },
  [`${API_URL}/orgs`]: {
    method: "GET",
  },
};

export const parameteredEndpoints: Record<string, RequestParams> = {
  [`${API_URL}/tasks/:taskID`]: {
    method: "GET",
  },
  [`${API_URL}/auth/check-username?username=:username`]: {
    method: "GET",
    public: true,
  },
  [`${API_URL}/auth/account/confirm?email=:email&token=:token`]: {
    method: "POST",
    public: true,
  },
  [`${API_URL}/auth/account/confirm/retry?email=:email`]: {
    method: "POST",
    public: true,
  },
  [`${API_URL}/auth/logout`]: {
    method: "POST",
  },
};

export function resolveEndpointConfig(url: string): RequestParams {
  // If the endpoint URL is parameterless, it can be directly mapped from the 'parameterLessEndpoints' object
  if (parameterLessEndpoints[url]) return parameterLessEndpoints[url];

  // If endpoint URL is parametered resolve it from 'parameteredEndpoints' object
  for (const [pattern, config] of Object.entries(parameteredEndpoints)) {
    const relativePattern = pattern.replace(API_URL, "");

    // A fictive regular expression is created to ensure that the correct parametrized URL is matched.
    // The question mark replacement is dedicated to query-parametrized URLs. In this case, it is made sure it is treated as a literal character, instead of special one (in Regex language).
    const regex = new RegExp(
      relativePattern.replace(/:\w+/g, "[^/]+").replace("?", "\\?"),
    );

    // Return the config object of the matched URL
    if (regex.test(url)) return config;
  }

  throw new Error(`Configuration not found for the endpoint: ${url}`);
}
