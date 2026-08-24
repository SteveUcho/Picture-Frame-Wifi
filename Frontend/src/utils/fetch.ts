export const fetchWithBackend = (url: string, options?: RequestInit) => {
  return fetch(import.meta.env.PUBLIC_API_URL + url, {
    headers: {
      ...options?.headers,
      'Content-Type': 'application/json'
    },
    ...options
  });
};
