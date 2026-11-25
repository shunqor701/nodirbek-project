let csrfToken = "";
let sessionRequest;

export async function api(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  let body = options.body;
  if (body && !(body instanceof FormData) && typeof body !== "string") {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && csrfToken) {
    headers.set("X-CSRFToken", csrfToken);
  }

  const response = await fetch(`/api${path}`, {
    ...options,
    method,
    headers,
    body,
    credentials: "same-origin",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "So‘rovni bajarib bo‘lmadi.");
  }
  return payload;
}

export function getSession() {
  if (!sessionRequest) {
    sessionRequest = api("/session").then((data) => {
      csrfToken = data.csrfToken;
      return data;
    });
  }
  return sessionRequest;
}
