import type {
  LocationsResponse,
  RecommendationRequest,
  RecommendationsResponse,
} from '../types/api'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

export class ApiError extends Error {
  public readonly statusCode: number
  public readonly detail: unknown

  constructor(statusCode: number, detail: unknown) {
    super(
      typeof detail === 'string'
        ? detail
        : `Permintaan API gagal (HTTP ${statusCode}).`,
    )
    this.statusCode = statusCode
    this.detail = detail
    this.name = 'ApiError'
  }
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  let payload: unknown

  try {
    payload = await response.json()
  } catch {
    if (!response.ok) {
      throw new ApiError(
        response.status,
        `API mengembalikan HTTP ${response.status} tanpa detail JSON.`,
      )
    }
    throw new Error('Respons API bukan JSON yang valid.')
  }

  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload !== null && 'detail' in payload
        ? payload.detail
        : payload
    throw new ApiError(response.status, detail)
  }

  return payload as T
}

export function getLocations(): Promise<LocationsResponse> {
  return requestJson<LocationsResponse>('/api/mobility/locations')
}

export function getRecommendations(
  request: RecommendationRequest,
): Promise<RecommendationsResponse> {
  return requestJson<RecommendationsResponse>(
    '/api/meal-planning/recommendations',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    },
  )
}
