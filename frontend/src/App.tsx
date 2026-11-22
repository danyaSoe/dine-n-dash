import { useEffect, useState } from 'react'

import RecommendationResults from './components/RecommendationResults'
import { ApiError, getLocations, getRecommendations } from './services/api'
import {
  buildRecommendationRequest,
  validateMealPlannerForm,
  type MealPlannerFormErrors,
  type MealPlannerFormValues,
} from './services/mealPlannerForm'
import type {
  Location,
  RecommendationRequest,
  RecommendationsResponse,
} from './types/api'
import './App.css'

const initialFormValues: MealPlannerFormValues = {
  origin: '',
  destination: '',
  ready_time: '11:40',
  class_start: '12:30',
  buffer_minutes: '5',
  meal_mode: 'dine_in',
  meal_duration_minutes: '18',
}

const formFieldOrder = [
  'origin',
  'destination',
  'ready_time',
  'class_start',
  'buffer_minutes',
  'meal_duration_minutes',
] as const

const fieldInputIds: Record<(typeof formFieldOrder)[number], string> = {
  origin: 'origin',
  destination: 'destination',
  ready_time: 'ready-time',
  class_start: 'class-start',
  buffer_minutes: 'buffer-minutes',
  meal_duration_minutes: 'meal-duration',
}

function getLocationErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.statusCode === 503) {
      return 'Layanan lokasi sedang tidak tersedia. Coba lagi sebentar.'
    }
    if (typeof error.detail === 'string') {
      return error.detail
    }
  }

  return 'Lokasi belum dapat dimuat. Periksa koneksi ke API Gateway, lalu coba lagi.'
}

function requestLocations(): Promise<Location[]> {
  return getLocations().then((response) => response.locations)
}

function getValidationMessages(detail: unknown): string[] {
  if (!Array.isArray(detail)) {
    return []
  }

  return detail.flatMap((item: unknown) => {
    if (
      typeof item === 'object' &&
      item !== null &&
      'msg' in item &&
      typeof item.msg === 'string'
    ) {
      return [item.msg]
    }

    return []
  })
}

function getRecommendationError(error: unknown): {
  title: string
  message: string
} {
  if (error instanceof ApiError) {
    if (error.statusCode === 422) {
      const details = getValidationMessages(error.detail)
      return {
        title: 'Periksa kembali data rencanamu',
        message:
          details.join(' ') ||
          (typeof error.detail === 'string'
            ? error.detail
            : 'Ada data yang belum sesuai. Periksa waktu, lokasi, dan durasi makan.'),
      }
    }

    if (error.statusCode === 503 || error.statusCode >= 500) {
      return {
        title: 'Layanan rekomendasi belum tersedia',
        message:
          'API Gateway atau layanan perhitungan sedang tidak dapat dihubungi. Coba lagi sebentar.',
      }
    }

    if (typeof error.detail === 'string') {
      return {
        title: 'Permintaan belum dapat diproses',
        message: error.detail,
      }
    }
  }

  if (error instanceof TypeError) {
    return {
      title: 'Koneksi ke API Gateway gagal',
      message: 'Periksa koneksi lalu coba kirim permintaan kembali.',
    }
  }

  return {
    title: 'Terjadi kendala saat mencari rekomendasi',
    message:
      error instanceof Error
        ? error.message
        : 'Coba lagi setelah memeriksa data rencanamu.',
  }
}

function App() {
  const [locations, setLocations] = useState<Location[]>([])
  const [locationsLoading, setLocationsLoading] = useState(true)
  const [locationsError, setLocationsError] = useState('')
  const [formValues, setFormValues] =
    useState<MealPlannerFormValues>(initialFormValues)
  const [fieldErrors, setFieldErrors] = useState<MealPlannerFormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [recommendationResponse, setRecommendationResponse] =
    useState<RecommendationsResponse | null>(null)
  const [submittedRequest, setSubmittedRequest] =
    useState<RecommendationRequest | null>(null)
  const [recommendationError, setRecommendationError] = useState<{
    title: string
    message: string
  } | null>(null)

  useEffect(() => {
    let active = true

    void requestLocations()
      .then((loadedLocations) => {
        if (active) {
          setLocations(loadedLocations)
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setLocations([])
          setLocationsError(getLocationErrorMessage(error))
        }
      })
      .finally(() => {
        if (active) {
          setLocationsLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  async function reloadLocations() {
    setLocationsLoading(true)
    setLocationsError('')

    try {
      setLocations(await requestLocations())
    } catch (error: unknown) {
      setLocations([])
      setLocationsError(getLocationErrorMessage(error))
    } finally {
      setLocationsLoading(false)
    }
  }

  const canPlan = !locationsLoading && !locationsError && locations.length > 0

  function updateField<Field extends keyof MealPlannerFormValues>(
    field: Field,
    value: MealPlannerFormValues[Field],
  ) {
    setFormValues((current) => ({ ...current, [field]: value }))
    setFieldErrors((current) => ({ ...current, [field]: undefined }))
    setRecommendationResponse(null)
    setSubmittedRequest(null)
    setRecommendationError(null)
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const errors = validateMealPlannerForm(formValues, locations)
    setFieldErrors(errors)
    setRecommendationResponse(null)
    setSubmittedRequest(null)
    setRecommendationError(null)

    if (Object.keys(errors).length > 0) {
      const firstInvalidField = formFieldOrder.find((field) => errors[field])
      if (firstInvalidField) {
        document.getElementById(fieldInputIds[firstInvalidField])?.focus()
      }
      return
    }

    const request = buildRecommendationRequest(formValues)
    setIsSubmitting(true)

    try {
      const response = await getRecommendations(request)
      setSubmittedRequest(request)
      setRecommendationResponse(response)
    } catch (error: unknown) {
      setRecommendationError(getRecommendationError(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  function fieldError(field: keyof MealPlannerFormValues): string | undefined {
    return fieldErrors[field]
  }

  return (
    <div className="app-page">
      <header className="site-header">
        <div className="content-width header-content">
          <a className="brand" href="/" aria-label="Dine-N-Dash, halaman utama">
            <span className="brand-mark" aria-hidden="true">
              D
            </span>
            <span>Dine-N-Dash</span>
          </a>
          <p className="header-tagline">
            Temukan waktu makan di sela jadwal kuliah
          </p>
        </div>
      </header>

      <main className="content-width page-content">
        <section className="page-intro" aria-labelledby="page-title">
          <p className="eyebrow">Perencana waktu makan kampus</p>
          <h1 id="page-title">Atur waktu makan di sela kelas</h1>
          <p className="intro-copy">
            Rencanakan jedamu dengan mempertimbangkan perjalanan, waktu tunggu,
            durasi makan, dan kelas berikutnya.
          </p>
        </section>

        <aside className="sample-notice" aria-label="Informasi data">
          <span className="notice-mark" aria-hidden="true">
            i
          </span>
          <p>
            Data lokasi, rute, restoran, jam buka, dan waktu tunggu saat ini
            masih berupa <strong>sample/mock</strong>.
          </p>
        </aside>

        <section className="planner-card" aria-labelledby="planner-title">
          <div className="planner-heading">
            <div>
              <p className="eyebrow">Mulai rencanakan</p>
              <h2 id="planner-title">Rencanakan waktu makan</h2>
            </div>
          </div>
          <p className="planner-description">
            Waktu awal hanya contoh untuk memudahkan pengujian. Sesuaikan
            dengan jadwalmu; formulir tidak dikirim otomatis.
          </p>

          {locationsLoading && (
            <p className="location-status" role="status" aria-live="polite">
              <span className="loading-dot" aria-hidden="true" />
              Memuat pilihan lokasi dari layanan kampus…
            </p>
          )}

          {locationsError && (
            <div className="location-error" role="alert">
              <p>{locationsError}</p>
              <button
                className="retry-button"
                type="button"
                onClick={() => void reloadLocations()}
              >
                Coba muat ulang
              </button>
            </div>
          )}

          {!locationsLoading && !locationsError && locations.length === 0 && (
            <p className="location-error" role="alert">
              Layanan belum menyediakan pilihan lokasi.
            </p>
          )}

          <form
            className="planner-form"
            noValidate
            aria-busy={isSubmitting}
            onSubmit={handleSubmit}
          >
            {Object.values(fieldErrors).some(Boolean) && (
              <div className="field-error-summary" role="alert">
                Periksa kembali kolom yang ditandai sebelum melanjutkan.
              </div>
            )}
            <fieldset
              className="form-fields"
              disabled={!canPlan || isSubmitting}
            >
              <legend className="visually-hidden">
                Informasi rencana makan
              </legend>

              <div className="form-section">
                <div className="form-section-heading">
                  <span className="section-index" aria-hidden="true">
                    1
                  </span>
                  <div>
                    <h3>Lokasi perjalanan</h3>
                    <p>Pilih titik awal dan gedung kelas tujuan.</p>
                  </div>
                </div>

                <div className="field-grid">
                  <div className="form-field">
                    <label htmlFor="origin">Lokasi keberangkatan</label>
                    <select
                      id="origin"
                      autoComplete="off"
                      value={formValues.origin}
                      aria-invalid={Boolean(fieldError('origin'))}
                      aria-describedby={
                        fieldError('origin') ? 'origin-error' : undefined
                      }
                      onChange={(event) =>
                        updateField('origin', event.target.value)
                      }
                    >
                      <option value="">Pilih lokasi</option>
                      {locations.map((location) => (
                        <option key={location.id} value={location.name}>
                          {location.name}
                        </option>
                      ))}
                    </select>
                    {fieldError('origin') && (
                      <p className="field-error" id="origin-error">
                        {fieldError('origin')}
                      </p>
                    )}
                  </div>

                  <div className="form-field">
                    <label htmlFor="destination">Gedung kelas berikutnya</label>
                    <select
                      id="destination"
                      autoComplete="off"
                      value={formValues.destination}
                      aria-invalid={Boolean(fieldError('destination'))}
                      aria-describedby={
                        fieldError('destination')
                          ? 'destination-error'
                          : undefined
                      }
                      onChange={(event) =>
                        updateField('destination', event.target.value)
                      }
                    >
                      <option value="">Pilih gedung</option>
                      {locations.map((location) => (
                        <option key={location.id} value={location.name}>
                          {location.name}
                        </option>
                      ))}
                    </select>
                    {fieldError('destination') && (
                      <p className="field-error" id="destination-error">
                        {fieldError('destination')}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="form-section">
                <div className="form-section-heading">
                  <span className="section-index" aria-hidden="true">
                    2
                  </span>
                  <div>
                    <h3>Jadwal kelas</h3>
                    <p>Gunakan waktu lokal untuk rencana hari ini.</p>
                  </div>
                </div>

                <div className="field-grid field-grid-three">
                  <div className="form-field">
                    <label htmlFor="ready-time">Waktu siap berangkat</label>
                    <input
                      id="ready-time"
                      type="time"
                      required
                      value={formValues.ready_time}
                      aria-invalid={Boolean(fieldError('ready_time'))}
                      aria-describedby={
                        fieldError('ready_time') ? 'ready-time-error' : undefined
                      }
                      onChange={(event) =>
                        updateField('ready_time', event.target.value)
                      }
                    />
                    {fieldError('ready_time') && (
                      <p className="field-error" id="ready-time-error">
                        {fieldError('ready_time')}
                      </p>
                    )}
                  </div>

                  <div className="form-field">
                    <label htmlFor="class-start">Kelas dimulai pukul</label>
                    <input
                      id="class-start"
                      type="time"
                      required
                      value={formValues.class_start}
                      aria-invalid={Boolean(fieldError('class_start'))}
                      aria-describedby={
                        fieldError('class_start')
                          ? 'class-start-error'
                          : undefined
                      }
                      onChange={(event) =>
                        updateField('class_start', event.target.value)
                      }
                    />
                    {fieldError('class_start') && (
                      <p className="field-error" id="class-start-error">
                        {fieldError('class_start')}
                      </p>
                    )}
                  </div>

                  <div className="form-field">
                    <label htmlFor="buffer-minutes">
                      Buffer kedatangan
                    </label>
                    <div className="input-with-unit">
                      <input
                        id="buffer-minutes"
                        type="number"
                        min="0"
                        step="1"
                        inputMode="numeric"
                        required
                        value={formValues.buffer_minutes}
                        aria-invalid={Boolean(fieldError('buffer_minutes'))}
                        aria-describedby={
                          fieldError('buffer_minutes')
                            ? 'buffer-minutes-error'
                            : 'buffer-minutes-hint'
                        }
                        onChange={(event) =>
                          updateField('buffer_minutes', event.target.value)
                        }
                      />
                      <span>menit</span>
                    </div>
                    <p className="field-hint" id="buffer-minutes-hint">
                      Waktu tambahan sebelum kelas dimulai.
                    </p>
                    {fieldError('buffer_minutes') && (
                      <p className="field-error" id="buffer-minutes-error">
                        {fieldError('buffer_minutes')}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="form-section meal-section">
                <div className="form-section-heading">
                  <span className="section-index" aria-hidden="true">
                    3
                  </span>
                  <div>
                    <h3>Cara makan</h3>
                    <p>Pilih cara makan yang sesuai dengan jedamu.</p>
                  </div>
                </div>

                <div className="meal-options" role="group" aria-label="Cara makan">
                  <label
                    className={`meal-option${formValues.meal_mode === 'dine_in' ? ' selected' : ''}`}
                  >
                    <input
                      type="radio"
                      name="meal-mode"
                      value="dine_in"
                      checked={formValues.meal_mode === 'dine_in'}
                      onChange={() => updateField('meal_mode', 'dine_in')}
                    />
                    <span className="radio-indicator" aria-hidden="true" />
                    <span>
                      <strong>Makan di tempat</strong>
                      <small>Tambahkan durasi untuk makan di lokasi.</small>
                    </span>
                  </label>
                  <label
                    className={`meal-option${formValues.meal_mode === 'takeaway' ? ' selected' : ''}`}
                  >
                    <input
                      type="radio"
                      name="meal-mode"
                      value="takeaway"
                      checked={formValues.meal_mode === 'takeaway'}
                      onChange={() => updateField('meal_mode', 'takeaway')}
                    />
                    <span className="radio-indicator" aria-hidden="true" />
                    <span>
                      <strong>Bawa pulang</strong>
                      <small>Tanpa durasi makan di tempat.</small>
                    </span>
                  </label>
                </div>

                {formValues.meal_mode === 'dine_in' && (
                  <div className="form-field duration-field">
                    <label htmlFor="meal-duration">Durasi makan</label>
                    <div className="input-with-unit">
                      <input
                        id="meal-duration"
                        type="number"
                        min="0"
                        step="1"
                        inputMode="numeric"
                        required
                        value={formValues.meal_duration_minutes}
                        aria-invalid={Boolean(
                          fieldError('meal_duration_minutes'),
                        )}
                        aria-describedby={
                          fieldError('meal_duration_minutes')
                            ? 'meal-duration-error'
                            : undefined
                        }
                        onChange={(event) =>
                          updateField(
                            'meal_duration_minutes',
                            event.target.value,
                          )
                        }
                      />
                      <span>menit</span>
                    </div>
                    {fieldError('meal_duration_minutes') && (
                      <p className="field-error" id="meal-duration-error">
                        {fieldError('meal_duration_minutes')}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </fieldset>

            <div className="form-footer">
              <button
                className="submit-button"
                type="submit"
                disabled={!canPlan || isSubmitting}
              >
                {isSubmitting ? 'Mencari rekomendasi…' : 'Cari rekomendasi'}
                {!isSubmitting && <span aria-hidden="true">→</span>}
              </button>
            </div>
          </form>
        </section>

        {isSubmitting && (
          <p className="search-status" role="status" aria-live="polite">
            <span className="loading-dot" aria-hidden="true" />
            Menghitung pilihan yang sesuai dengan jadwalmu…
          </p>
        )}

        {recommendationError && (
          <section className="api-error" role="alert">
            <h2>{recommendationError.title}</h2>
            <p>{recommendationError.message}</p>
          </section>
        )}

        {recommendationResponse && submittedRequest && (
          <RecommendationResults
            response={recommendationResponse}
            request={submittedRequest}
          />
        )}
      </main>
    </div>
  )
}

export default App
