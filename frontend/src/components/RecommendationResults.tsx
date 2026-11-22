import type {
  RecommendationRequest,
  RecommendationsResponse,
} from '../types/api'

interface RecommendationResultsProps {
  response: RecommendationsResponse
  request: RecommendationRequest
}

function RecommendationResults({
  response,
  request,
}: RecommendationResultsProps) {
  const hasRecommendations =
    response.success && response.recommendations.length > 0

  return (
    <section className="results-section" aria-labelledby="results-title">
      <div className="results-heading">
        <div>
          <p className="eyebrow">Rencana makanmu</p>
          <h2 id="results-title">Hasil rekomendasi</h2>
        </div>
        {hasRecommendations && (
          <span className="result-count">
            {response.recommendations.length} pilihan
          </span>
        )}
      </div>

      <section className="schedule-summary" aria-label="Ringkasan jadwal">
        <div className="summary-route">
          <span>Perjalanan</span>
          <strong>
            {request.origin} <span aria-hidden="true">→</span>{' '}
            {request.destination}
          </strong>
        </div>
        <div>
          <span>Siap berangkat</span>
          <strong>{request.ready_time}</strong>
        </div>
        <div>
          <span>Kelas dimulai</span>
          <strong>{request.class_start}</strong>
        </div>
        <div>
          <span>Buffer kedatangan</span>
          <strong>{request.buffer_minutes} menit</strong>
        </div>
        <div>
          <span>Cara makan</span>
          <strong>
            {request.meal_mode === 'dine_in'
              ? `Makan di tempat · ${request.meal_duration_minutes} menit`
              : 'Bawa pulang'}
          </strong>
        </div>
      </section>

      {!hasRecommendations && (
        <div className="no-results" role="status">
          <span className="empty-mark" aria-hidden="true">
            —
          </span>
          <h3>Belum ada tempat makan yang cocok dengan jadwalmu.</h3>
          <p>
            Coba sesuaikan lokasi, waktu, buffer, atau cara makan lalu cari
            kembali.
          </p>
          <a href="#planner-title">Ubah rencana di atas</a>
        </div>
      )}

      {hasRecommendations && (
        <div className="recommendation-list">
          {response.recommendations.map((recommendation) => (
            <article
              className="recommendation-card"
              key={recommendation.restaurant_id}
            >
              <div className="recommendation-top">
                <div>
                  <p className="restaurant-label">Tempat makan</p>
                  <h3>{recommendation.restaurant_name}</h3>
                </div>
                <div
                  className="remaining-time"
                  aria-label={`Sisa waktu ${recommendation.remaining_minutes} menit`}
                >
                  <strong>{recommendation.remaining_minutes}</strong>
                  <span>menit tersisa</span>
                </div>
              </div>

              <div className="departure-deadline">
                <span>Paling lambat berangkat dari tempat makan</span>
                <strong>{recommendation.departure_deadline}</strong>
              </div>

              <dl className="recommendation-details">
                <div>
                  <dt>Perjalanan ke tempat makan</dt>
                  <dd>{recommendation.travel_to_restaurant_minutes} menit</dd>
                </div>
                <div>
                  <dt>Menunggu pesanan</dt>
                  <dd>{recommendation.waiting_minutes} menit</dd>
                </div>
                <div>
                  <dt>Durasi makan</dt>
                  <dd>
                    {recommendation.meal_duration_minutes} menit
                    {request.meal_mode === 'takeaway' &&
                      recommendation.meal_duration_minutes === 0 &&
                      ' (tidak makan di tempat)'}
                  </dd>
                </div>
                <div>
                  <dt>Perjalanan ke kelas</dt>
                  <dd>{recommendation.travel_to_class_minutes} menit</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      )}

      {response.unavailable_reasons.length > 0 && (
        <aside
          className="unavailable-reasons"
          aria-labelledby="unavailable-title"
        >
          <h3 id="unavailable-title">Tempat yang tidak memenuhi kriteria</h3>
          <ul>
            {response.unavailable_reasons.map((reason, index) => (
              <li key={`${reason}-${index}`}>{reason}</li>
            ))}
          </ul>
        </aside>
      )}
    </section>
  )
}

export default RecommendationResults
