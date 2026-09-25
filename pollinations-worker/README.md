# FBPro Pollinations Video Proxy

This Cloudflare Worker keeps the Pollinations API key server-side and exposes a small endpoint for Make.

## Endpoint

GET /video?prompt=YOUR_PROMPT&model=seedance-2.0-fast&duration=8&aspectRatio=9:16

## Required secret

Create a Cloudflare Worker secret named:

POLLINATIONS_API_KEY

The value is the full Pollinations API key. Do not put the key in this repository.

## Health check

GET /health

Expected:

{"ok":true,"service":"pollinations-video-proxy"}

## Make configuration

Replace the current Pollinations HTTP module with a normal HTTP GET request:

URL:
https://YOUR-WORKER.workers.dev/video

Query parameters:
prompt = {{encodeURL(1.prompt)}}
model = seedance-2.0-fast
duration = 8
aspectRatio = 9:16

The Worker returns the MP4 response body. Make can then pass that binary body to Google Drive.

## Deployment

From this directory with Wrangler installed:

wrangler secret put POLLINATIONS_API_KEY
wrangler deploy

Or use the Cloudflare dashboard to create a Worker from this source and add the secret under Settings > Variables and Secrets.
