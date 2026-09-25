export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "pollinations-video-proxy" });
    }

    if (request.method !== "GET" || url.pathname !== "/video") {
      return json({ ok: false, error: "Use GET /video?prompt=..." }, 404);
    }

    const prompt = url.searchParams.get("prompt");
    if (!prompt) return json({ ok: false, error: "Missing prompt" }, 400);

    if (!env.POLLINATIONS_API_KEY) {
      return json({ ok: false, error: "POLLINATIONS_API_KEY is not configured" }, 500);
    }

    const upstream = new URL("https://gen.pollinations.ai/video/" + encodeURIComponent(prompt));
    for (const name of ["model", "duration", "aspectRatio"]) {
      const value = url.searchParams.get(name);
      if (value) upstream.searchParams.set(name, value);
    }

    const response = await fetch(upstream, {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + env.POLLINATIONS_API_KEY,
        "Accept": "video/mp4"
      }
    });

    const headers = new Headers(response.headers);
    headers.set("Cache-Control", "no-store");
    headers.set("Access-Control-Allow-Origin", "*");

    return new Response(response.body, {
      status: response.status,
      headers
    });
  }
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store"
    }
  });
}
