const apiBaseUrl = import.meta.env.PUBLIC_API_URL;

export const swrFetcher = (...args: [string, RequestInit?]) => fetchWithBackend(...args).then(res => res.json())

// Check if all required URL parameters are satisfied
export const urlKeysSatisfied = (url: string, urlVars: Record<string, string>) => {
  const urlKeys = url.match(/:\w+/g);
  if (!urlKeys) return true;
  return urlKeys.every(key => urlVars[key.slice(1)]);
}

export const generateUrl = (url: string, urlVars: Record<string, string>) => {
  if (!urlKeysSatisfied(url, urlVars)) return null;
  let result = url;
  for (const [key, value] of Object.entries(urlVars)) {
    result = result.replace(`:${key}`, value);
  }
  return result;
}

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
