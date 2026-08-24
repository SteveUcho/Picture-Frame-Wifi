const apiBaseUrl = import.meta.env.PUBLIC_API_URL;

export const fetchWithBackend = (url: string, options?: RequestInit) => {
  const { headers, ...rest } = options || {};
  return fetch(apiBaseUrl + url, {
    headers: {
      ...headers,
      'Content-Type': 'application/json'
    },
    ...rest
  });
};
