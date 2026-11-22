# Dine-N-Dash Frontend

Frontend React + TypeScript built with Vite. The current stage provides the
Meal Planner form, Mobility-backed location choices, client-side validation,
typed API foundations, and recommendation results from the backend.

## Local development

Requirements: Node.js 20.19+ and npm.

From the repository root, start the backend API Gateway:

```powershell
docker compose up -d
Set-Location frontend
npm ci
npm run dev
```

Vite prints the local URL when the development server starts. No `.env` file
is needed for the default setup: `/api` requests are proxied to
`http://localhost:8080`. To use another gateway, set
`VITE_API_PROXY_TARGET`. Set `VITE_API_BASE_URL` only if requests should bypass
the Vite proxy and use a different API base URL.

The backend sample locations, restaurants, routes, opening hours, and waiting
times are not live operational data. Authentication, booking, and restaurant
catalog features are not implemented.

## Checks

```powershell
Set-Location frontend
npm run lint
npm test
npm run build
```
