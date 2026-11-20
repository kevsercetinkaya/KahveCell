# KahveCell

Ankara icin kahve aboneligi ve siparis takip uygulamasi. Backend FastAPI ve SQLite, web arayuzu React/Vite, harita Leaflet kullanir.

## Özellikler

- Telefon numarasi ve OTP (`1234`) ile kayit/giris; JWT access ve refresh token oturumu
- Starter, Premium ve Unlimited abonelikleri; yalnizca test kartlarini kabul eden Paycell odeme simulasyonu
- Ankara seed dukkânlari, urun/menus, isim-adres aramasi ve Haversine ile yakinlik siralamasi
- Abonelik kredisi kontrolu, siparis ozellestirme, durum takibi ve imzali HMAC-SHA256 QR kodu
- Müşteri sayfalari: giris, kayit, kesif haritasi, dukkan detayi, siparis, QR, gecmis ve abonelik

## Teknolojiler

- Backend: Python 3.12+, FastAPI, SQLAlchemy, SQLite
- Frontend: React, Vite, React Router, Leaflet / React Leaflet
- QR: qrcode + Pillow; kart bilgileri veritabaninda tutulmaz

## Proje Yapisi

```text
backend/
  app/api/v1/       # Versiyonlu REST endpointleri
  app/core/         # Ayarlar, token guvenligi ve plan katalogu
  app/models/       # SQLAlchemy tablolar ve iliskiler
  app/schemas/      # API istek/yanit semalari
  app/services/     # Abonelik, siparis ve QR is mantigi
  app/seed_data.py  # Idempotent Ankara demo verileri
frontend/
  src/api/          # Backend istemcisi ve refresh token yonetimi
  src/app/          # Auth provider ve React Router
  src/components/   # Ortak arayuz bilesenleri
  src/pages/        # Uygulama sayfalari
```

## Gereksinimler

- Python 3.12 veya ustu
- Node.js 20.19 veya ustu ve npm

## Kurulum ve Calistirma

Komutlari proje kok klasorunde (`kahvecell/`) calistir.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
openssl rand -hex 32
```

`openssl` komutunun urettigi degeri `backend/.env` icindeki `JWT_SECRET_KEY` alanina yaz. Bu dosyayi GitHub'a ekleme; `.gitignore` disarida tutar. Ardindan, proje kokune donmeden backend klasorundeyken:

```bash
uvicorn app.main:app --reload --reload-dir app
```

Ilk acilista SQLite dosyasi ve eksik tablolar otomatik olusturulur; Ankara dukkanlari, menu urunleri, demo Starter musterisi ve demo dukkan sahibi idempotent olarak eklenir. API dokumantasyonu: <http://localhost:8000/docs>.

### Frontend

Yeni bir terminal acip proje kok klasorunden:

```bash
npm install --prefix frontend
npm run dev --prefix frontend
```

Vite adresi: <http://localhost:5173>. Backend adresini degistirmen gerekirse `frontend/.env.example` dosyasini `.env.local` olarak kopyalayip `VITE_API_BASE_URL` degerini ayarlayabilirsin.

### Kontroller

```bash
npm run lint --prefix frontend
npm run build --prefix frontend
```

## Demo Girisleri

- Musteri: `+905550000001`
- Dukkan sahibi: `+905550000002`
- Simule OTP: `1234`
- Basarili odeme karti: `4242-4242-4242-4242`
- Basarisiz odeme karti: `4000-0000-0000-0002`

Gercek SMS veya odeme yapilmaz. Gercek kart numarasi ya da CVV girmeyin. Bu bilgiler kaydedilmez.

## GitHub Guvenligi

`.env`, sanal ortamlar, SQLite veritabani, `node_modules` ve Vite `dist` ciktisi `.gitignore` ile disarida tutulur. Yalnizca `.env.example` dosyalari paylasilmalidir. Ankara seed verisi uygulama baslangicinda yeniden eklenmeye calisilsa da mevcut kayitlari cogaltmaz.
