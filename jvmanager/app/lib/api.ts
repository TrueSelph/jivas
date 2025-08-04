
import { redirect } from "react-router";

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem("jivas-token");

  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem("jivas-token");
    localStorage.removeItem("jivas-token-exp");
    // Using window.location to force a full page reload to clear any in-memory state.
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    // Throw an error to stop further processing
    throw new Response("Unauthorized", { status: 401 });
  }

  return response;
}
