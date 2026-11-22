export type MealMode = 'dine_in' | 'takeaway'

export interface Location {
  id: string
  name: string
}

export interface LocationsResponse {
  data_source: 'sample'
  locations: Location[]
}

interface RecommendationRequestBase {
  origin: string
  destination: string
  ready_time: string
  class_start: string
  buffer_minutes: number
}

export type RecommendationRequest = RecommendationRequestBase &
  (
    | {
        meal_mode: 'dine_in'
        meal_duration_minutes: number
      }
    | {
        meal_mode: 'takeaway'
        meal_duration_minutes?: never
      }
  )

export interface Recommendation {
  restaurant_id: string
  restaurant_name: string
  travel_to_restaurant_minutes: number
  waiting_minutes: number
  meal_duration_minutes: number
  travel_to_class_minutes: number
  departure_deadline: string
  remaining_minutes: number
}

export interface RecommendationsResponse {
  success: boolean
  recommendations: Recommendation[]
  unavailable_reasons: string[]
}
