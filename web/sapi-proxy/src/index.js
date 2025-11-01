export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const target = `https://api.scratch.mit.edu${url.pathname}${url.search}`;

    const cache = caches.default;
    let response = await cache.match(request); // try retrieving the response from cloudflare cache

    if (!response) {
      // if not cached, fetch from the real api
      response = await fetch(target, {
        headers: { "User-Agent": "Scratch-RemixTree-Proxy" },
      });

      // copy body + headers
      const corsResponse = new Response(await response.text(), {
        status: response.status,
        statusText: response.statusText,
      });

      corsResponse.headers.set("Access-Control-Allow-Origin", "*");
      corsResponse.headers.set(
        "Access-Control-Allow-Methods",
        "GET,POST,OPTIONS"
      );
      corsResponse.headers.set("Access-Control-Allow-Headers", "*");

      // cf edge cache
      corsResponse.headers.set(
        "Cache-Control",
        "public, s-maxage=86400, stale-while-revalidate=3600"
      );

      // store in there
      ctx.waitUntil(cache.put(request, corsResponse.clone()));

      response = corsResponse;
    }

    return response;
  },
};
