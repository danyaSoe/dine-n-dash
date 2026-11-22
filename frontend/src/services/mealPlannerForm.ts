import type { Location, RecommendationRequest } from '../types/api'

export interface MealPlannerFormValues {
  origin: string
  destination: string
  ready_time: string
  class_start: string
  buffer_minutes: string
  meal_mode: 'dine_in' | 'takeaway'
  meal_duration_minutes: string
}

export type MealPlannerFormErrors = Partial<
  Record<keyof MealPlannerFormValues, string>
>

const isValidTime = (value: string): boolean =>
  /^([01]\d|2[0-3]):[0-5]\d$/.test(value)

const isNonNegativeInteger = (value: string): boolean =>
  /^\d+$/.test(value)

export function validateMealPlannerForm(
  values: MealPlannerFormValues,
  locations: Location[],
): MealPlannerFormErrors {
  const errors: MealPlannerFormErrors = {}
  const locationNames = new Set(locations.map((location) => location.name))

  if (!values.origin) {
    errors.origin = 'Pilih lokasi keberangkatan.'
  } else if (!locationNames.has(values.origin)) {
    errors.origin = 'Pilih lokasi dari daftar yang tersedia.'
  }

  if (!values.destination) {
    errors.destination = 'Pilih gedung kelas berikutnya.'
  } else if (!locationNames.has(values.destination)) {
    errors.destination = 'Pilih lokasi dari daftar yang tersedia.'
  }

  if (!isValidTime(values.ready_time)) {
    errors.ready_time = 'Masukkan waktu siap berangkat yang valid.'
  }

  if (!isValidTime(values.class_start)) {
    errors.class_start = 'Masukkan waktu mulai kelas yang valid.'
  } else if (
    isValidTime(values.ready_time) &&
    values.class_start <= values.ready_time
  ) {
    errors.class_start = 'Kelas harus dimulai setelah waktu siap berangkat.'
  }

  if (!isNonNegativeInteger(values.buffer_minutes)) {
    errors.buffer_minutes = 'Masukkan bilangan bulat minimal 0 menit.'
  }

  if (
    values.meal_mode === 'dine_in' &&
    !isNonNegativeInteger(values.meal_duration_minutes)
  ) {
    errors.meal_duration_minutes = 'Masukkan durasi makan minimal 0 menit.'
  }

  return errors
}

export function buildRecommendationRequest(
  values: MealPlannerFormValues,
): RecommendationRequest {
  const commonFields = {
    origin: values.origin,
    destination: values.destination,
    ready_time: values.ready_time,
    class_start: values.class_start,
    buffer_minutes: Number(values.buffer_minutes),
  }

  if (values.meal_mode === 'dine_in') {
    return {
      ...commonFields,
      meal_mode: 'dine_in',
      meal_duration_minutes: Number(values.meal_duration_minutes),
    }
  }

  return {
    ...commonFields,
    meal_mode: 'takeaway',
  }
}
