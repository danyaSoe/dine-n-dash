import { describe, expect, it } from 'vitest'

import {
  buildRecommendationRequest,
  validateMealPlannerForm,
  type MealPlannerFormValues,
} from './mealPlannerForm'
import type { Location } from '../types/api'

const locations: Location[] = [
  { id: 'LABTEK_V', name: 'Labtek V' },
  { id: 'LABTEK_VIII', name: 'Labtek VIII' },
]

const validValues: MealPlannerFormValues = {
  origin: 'Labtek V',
  destination: 'Labtek VIII',
  ready_time: '11:40',
  class_start: '12:30',
  buffer_minutes: '5',
  meal_mode: 'dine_in',
  meal_duration_minutes: '18',
}

describe('meal planner form', () => {
  it('builds the dine-in request with a numeric meal duration', () => {
    expect(buildRecommendationRequest(validValues)).toEqual({
      origin: 'Labtek V',
      destination: 'Labtek VIII',
      ready_time: '11:40',
      class_start: '12:30',
      buffer_minutes: 5,
      meal_mode: 'dine_in',
      meal_duration_minutes: 18,
    })
  })

  it('omits meal duration from takeaway requests', () => {
    expect(
      buildRecommendationRequest({ ...validValues, meal_mode: 'takeaway' }),
    ).toEqual({
      origin: 'Labtek V',
      destination: 'Labtek VIII',
      ready_time: '11:40',
      class_start: '12:30',
      buffer_minutes: 5,
      meal_mode: 'takeaway',
    })
  })

  it('rejects invalid time order, fractional minutes, and unknown locations', () => {
    const errors = validateMealPlannerForm(
      {
        ...validValues,
        origin: 'Unknown location',
        class_start: '11:40',
        buffer_minutes: '2.5',
      },
      locations,
    )

    expect(errors.origin).toBe('Pilih lokasi dari daftar yang tersedia.')
    expect(errors.class_start).toBe(
      'Kelas harus dimulai setelah waktu siap berangkat.',
    )
    expect(errors.buffer_minutes).toBe('Masukkan bilangan bulat minimal 0 menit.')
  })

  it('requires meal duration only for dine-in', () => {
    const dineInErrors = validateMealPlannerForm(
      { ...validValues, meal_duration_minutes: '' },
      locations,
    )
    const takeawayErrors = validateMealPlannerForm(
      {
        ...validValues,
        meal_mode: 'takeaway',
        meal_duration_minutes: '',
      },
      locations,
    )

    expect(dineInErrors.meal_duration_minutes).toBe(
      'Masukkan durasi makan minimal 0 menit.',
    )
    expect(takeawayErrors.meal_duration_minutes).toBeUndefined()
  })
})
