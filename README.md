# FMS Flyer Generator Service

A Flask + Puppeteer web service that generates custom fundraiser flyers for Forever Metal Studio.

## Endpoints

### `GET /health`
Returns service status.

### `POST /generate-flyer-b64`
Generates a flyer and returns it as a base64-encoded PNG in JSON.

**Request body:**
```json
{
  "api_key": "YOUR_API_KEY",
  "org_name": "Lincoln Elementary PTA",
  "start_date": "07/01/2026",
  "end_date": "07/14/2026",
  "fundraiser_code": "LINCOLNPTA"
}
```

**Response:**
```json
{
  "success": true,
  "filename": "LINCOLNPTA_flyer.png",
  "image_b64": "iVBORw0KGgo..."
}
```

## Environment Variables

- `FMS_API_KEY` — Secret key for API authentication (set in Render dashboard)
- `PORT` — Port to listen on (default: 10000)
- `PUPPETEER_EXECUTABLE_PATH` — Path to Chromium binary (default: /usr/bin/chromium)

## Deployment

Deploy to Render.com using the included Dockerfile.
Set `FMS_API_KEY` as an environment variable in the Render dashboard.
