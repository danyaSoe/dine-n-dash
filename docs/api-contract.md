# API Contract

Dokumen ini mencatat API yang benar-benar diimplementasikan untuk empat
microservice Dine-N-Dash. Seluruh daftar restoran, jam layanan, waktu tunggu,
lokasi, dan estimasi rute yang disediakan saat ini adalah data sample/mock.

## Health checks

Semua service memberikan HTTP 200 dari `GET /health`. Bentuk respons:

```json
{
  "status": "ok",
  "service": "campus-mobility-service"
}
```

Nilai `service` adalah `campus-mobility-service`, `food-service`,
`meal-planning-service`, atau `user-service`.

## Campus Mobility Service

| Method | Path | Respons |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/locations` | Daftar lokasi sample |
| GET | `/routes/estimate?origin=...&destination=...` | Waktu jalan kaki sample dalam menit |

`GET /locations` memberikan `data_source: "sample"` dan array lokasi berisi
`id` serta `name`. Lokasi saat ini: Labtek V, Labtek VIII, dan Warung A–E.

Contoh `GET /routes/estimate?origin=Labtek%20V&destination=Warung%20A`:

```json
{
  "data_source": "sample",
  "origin": "Labtek V",
  "destination": "Warung A",
  "walking_minutes": 7
}
```

Nama lokasi harus cocok persis dan peka huruf besar/kecil. Parameter kosong
atau whitespace ditolak dengan HTTP 422; lokasi yang tidak dikenal dan
pasangan yang tidak memiliki data rute menghasilkan HTTP 404 dengan `detail`
yang menjelaskan kendala. Lokasi yang sama menghasilkan 0 menit. Data rute
antar masing-masing Labtek dan Warung tersedia; rute Warung-ke-Warung tidak
tersedia. Rute sample dianggap dua arah dengan durasi sama.

## Food Service

| Method | Path | Respons |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/restaurants` | Daftar restoran sample |
| GET | `/restaurants/{restaurant_id}` | Detail restoran sample |
| GET | `/restaurants/{restaurant_id}/availability?arrival_time=HH:MM&meal_mode=dine_in\|takeaway` | Jam buka, mode, waktu tunggu |

Daftar merespons `data_source: "sample"` dan `restaurants`. Setiap restoran
berisi `id`, `name`, `opening_hours` (`opens_at`, `closes_at`), daftar
`supported_meal_modes`, dan `waiting_time_estimates` (`start_time`, `end_time`,
`minutes`). Detail restoran membungkus objek restoran dalam properti
`restaurant`, juga dengan `data_source: "sample"`. ID sample adalah `R001`
sampai `R005` dan nama sample Warung A sampai Warung E.

Contoh respons availability:

```json
{
  "data_source": "sample",
  "restaurant_id": "R001",
  "arrival_time": "11:40:00",
  "is_open": true,
  "meal_mode": "dine_in",
  "supports_meal_mode": true,
  "waiting_minutes": 8
}
```

`arrival_time` harus waktu lokal valid tanpa offset zona waktu. `meal_mode`
hanya menerima `dine_in` atau `takeaway`. Input invalid menghasilkan HTTP 422;
ID restoran tidak dikenal menghasilkan HTTP 404. Jam buka inklusif di awal dan
eksklusif di akhir (`opens_at <= arrival_time < closes_at`). Saat tutup,
`waiting_minutes` bernilai `null`. Status dukungan mode terpisah dari status
buka: restoran dapat merespons 200 dengan `supports_meal_mode: false`.
Rentang waktu tunggu memiliki batas awal inklusif dan akhir eksklusif.

Data jam, mode, dan perkiraan tunggu adalah mock yang diasumsikan berlaku setiap
hari. Endpoint memeriksa waktu kedatangan, bukan durasi layanan sampai tutup.

## Meal Planning Service

| Method | Path | Respons |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/recommendations` | Rekomendasi berdasarkan jadwal dan estimasi perjalanan |

Request:

```json
{
  "origin": "Labtek V",
  "destination": "Labtek VIII",
  "ready_time": "11:40",
  "class_start": "12:30",
  "buffer_minutes": 5,
  "meal_mode": "dine_in",
  "meal_duration_minutes": 18
}
```

`origin`/`destination` harus berupa nama non-whitespace (maksimum 100
karakter). Waktu berupa waktu lokal tanpa zona waktu dan presisi menit
(`HH:MM`); `class_start` harus setelah `ready_time` dalam hari yang sama.
`buffer_minutes` dan `meal_duration_minutes` (jika disediakan) berupa integer
non-negatif. `meal_mode` hanya `dine_in` atau `takeaway`; durasi makan wajib
untuk `dine_in`, sedangkan `takeaway` tidak menambahkan durasi makan di lokasi.
Input tidak valid menghasilkan HTTP 422.

Bentuk respons:

```json
{
  "success": true,
  "recommendations": [
    {
      "restaurant_id": "R001",
      "restaurant_name": "Warung A",
      "travel_to_restaurant_minutes": 7,
      "waiting_minutes": 8,
      "meal_duration_minutes": 18,
      "travel_to_class_minutes": 8,
      "departure_deadline": "12:17",
      "remaining_minutes": 4
    }
  ],
  "unavailable_reasons": []
}
```

Angka response tersebut merupakan contoh dari data sample, bukan estimasi
operasional. `success` bernilai true jika ada rekomendasi; jika tidak ada,
respons HTTP 200 berisi `success: false` dan array rekomendasi kosong.
Kandidat diurutkan dengan sisa waktu terbesar terlebih dahulu.

Meal Planning memanggil Food (`/restaurants`, `/availability`) dan Mobility
(`/routes/estimate`) melalui HTTP. `FOOD_SERVICE_URL` dan
`MOBILITY_SERVICE_URL` menentukan base URL. Default lokal masing-masing
`http://127.0.0.1:8002` dan `http://127.0.0.1:8001`; Docker Compose
menggantinya dengan hostname service Docker. `SERVICE_TIMEOUT_SECONDS`
menentukan timeout positif, default 3 detik. Dependency yang tidak tersedia,
memberikan status error selain route 404 Mobility, atau mengembalikan response
di luar kontrak menghasilkan HTTP 503. Route 404 Mobility diperlakukan sebagai
kendala kandidat dan dijelaskan dalam `unavailable_reasons`.

Batas kedatangan adalah `class_start - buffer_minutes`.
`remaining_minutes` adalah batas kedatangan dikurangi estimasi waktu tiba di
kelas. `departure_deadline` adalah batas kedatangan dikurangi perjalanan dari
restoran ke gedung kelas. Kandidat yang tiba saat restoran tutup, tidak
mendukung mode, selesai dilayani setelah tutup, terlambat, atau melewati tengah
malam tidak direkomendasikan. Rekomendasi tidak menyertakan properti
`data_source`; asal sample dijelaskan melalui kontrak/data dependency dan
dokumentasi.

## User Service

| Method | Path | Respons |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register` | Validasi input; HTTP 501 untuk input valid |
| POST | `/auth/login` | Validasi input; HTTP 501 untuk input valid |

Kedua request memakai `email` berformat email valid dan `password` 12–128
karakter. Input invalid menghasilkan HTTP 422. Nilai password tidak
dipantulkan pada respons error validasi. Input valid menghasilkan HTTP 501:
belum ada penyimpanan akun, password hashing, verifikasi kredensial, atau token.
Service tidak menyimpan password dan tidak memberi respons login sukses palsu.

## API Gateway lokal (Docker Compose)

Nginx adalah pintu masuk host pada `GATEWAY_PORT` (default 8080). Prefix
dihapus sebelum request diteruskan ke service internal:

| Prefix gateway | Service |
|---|---|
| `/api/mobility/` | Campus Mobility |
| `/api/food/` | Food |
| `/api/meal-planning/` | Meal Planning |
| `/api/users/` | User |

Contoh: `GET /api/mobility/health` diteruskan ke `GET /health`.
Port service internal tidak dipublikasikan langsung ke host.

## Asumsi dan batasan

- Data lokasi, restoran, rute, jam operasional, mode layanan, dan waktu tunggu
  merupakan sample/mock, bukan data nyata yang sudah diverifikasi.
- Estimasi rute dua arah dianggap sama. Tidak ada peta atau data jalur nyata.
- Jam restoran dianggap berlaku setiap hari; aturan hari libur tidak tersedia.
- Waktu diperlakukan lokal tanpa zona waktu. Jadwal lintas tengah malam tidak
  didukung.
- Meal Planning memastikan restoran buka saat tiba dan waktu selesai layanan
  tidak melewati jam tutup.
- Health check hanya memastikan aplikasi merespons, tidak memeriksa semua
  dependency.
- User Service hanya kerangka validasi; autentikasi/penyimpanan belum
  diimplementasikan.
- Docker/Nginx hanya untuk penggunaan lokal. STB, Cloudflare Tunnel, dan URL
  publik belum dikonfigurasi atau diuji.
