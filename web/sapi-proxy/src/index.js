export default {
  async fetch(request) {
    const targetUrl = new URL(request.url);
    targetUrl.hostname = "api.scratch.mit.edu";
    
    // give it to the real one
    const response = await fetch(targetUrl, request);
    
    // copy paste the actual response in a new Response object called corsResponse
    const corsResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
    
    // add corsies so it shouuuuuuld work from anywhere
    corsResponse.headers.set('Access-Control-Allow-Origin', '*');
    corsResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    corsResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    return corsResponse;
  },
};