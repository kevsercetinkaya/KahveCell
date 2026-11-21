import { useEffect, useState } from 'react'
import { Coffee, LocateFixed, MapPin, Search, SlidersHorizontal } from 'lucide-react'
import { Link } from 'react-router-dom'

import { apiRequest, ApiError } from '../api/client'
import ShopMap from '../components/ShopMap'

const money = new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 })

export default function HomePage() {
  const [shops, setShops] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [locating, setLocating] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [selectedShop, setSelectedShop] = useState(null)

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      const query = search.trim() ? `?q=${encodeURIComponent(search.trim())}` : ''
      setLoading(true)
      apiRequest(`/shops${query}`, { auth: false })
        .then((result) => {
          if (active) {
            setShops(result)
            setError('')
          }
        })
        .catch((requestError) => {
          if (active) setError(requestError instanceof ApiError ? requestError.message : 'Dükkânlar yüklenemedi.')
        })
        .finally(() => { if (active) setLoading(false) })
    }, search ? 220 : 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [search])

  function findNearby() {
    if (!navigator.geolocation) {
      setNotice('Tarayıcı konum bilgisini desteklemiyor.')
      return
    }
    setLocating(true)
    setNotice('')
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const query = new URLSearchParams({
            lat: String(coords.latitude),
            lng: String(coords.longitude),
            radius_km: '25',
          })
          const result = await apiRequest(`/shops?${query}`, { auth: false })
          setShops(result)
          setSelectedShop(null)
          setSearch('')
          setNotice(`${result.length} yakın nokta bulundu.`)
        } catch {
          setNotice('Yakındaki dükkânlar alınamadı.')
        } finally {
          setLocating(false)
        }
      },
      () => {
        setLocating(false)
        setNotice('Konum izni alınamadı; Ankara’daki noktalar gösteriliyor.')
      },
      { timeout: 10000, maximumAge: 60000 },
    )
  }

  return (
    <div className="page-stack home-page">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">ANKARA’DA BUGÜN</p>
          <h2>Bir kahve molası, iyi gelir.</h2>
          <p className="muted-copy">Yakınındaki anlaşmalı noktaları keşfet.</p>
        </div>
        <Link className="button button-dark" to="/subscription">Paketleri incele <span>→</span></Link>
      </section>

      <section className="discovery-layout">
        <div className="map-card">
          <div className="map-heading">
            <div><MapPin size={16} /><span>Ankara</span></div>
            <span className="map-live"><i /> {shops.length} nokta</span>
          </div>
          <div className="map-frame">
            {loading && shops.length === 0 ? (
              <div className="map-placeholder">Harita ve dükkânlar yükleniyor…</div>
            ) : (
              <ShopMap
                shops={shops}
                selectedShop={selectedShop}
                onSelect={setSelectedShop}
              />
            )}
          </div>
          <div className="map-attribution-note">Harita verisi © OpenStreetMap katkıda bulunanlar</div>
        </div>

        <aside className="discovery-panel">
          <div className="discovery-title-row">
            <div>
              <p className="eyebrow">KAHVE NOKTALARI</p>
              <h3>Yakınında keşfet</h3>
            </div>
            <span className="shop-count">{String(shops.length).padStart(2, '0')}</span>
          </div>
          <label className="search-box">
            <Search size={17} />
            <input
              type="search"
              value={search}
              onChange={(event) => {
                setSelectedShop(null)
                setSearch(event.target.value)
              }}
              placeholder="Semt veya dükkân ara"
              aria-label="Semt veya dükkân ara"
            />
            <SlidersHorizontal size={15} className="search-filter-icon" />
          </label>
          <button className="nearby-button" type="button" onClick={findNearby} disabled={locating}>
            <LocateFixed size={16} /> {locating ? 'Konum bulunuyor…' : 'Konumuma göre sırala'}
          </button>
          {notice && <p className="inline-notice" role="status">{notice}</p>}
          {error && <p className="form-error" role="alert">{error}</p>}

          <div className="shop-results" aria-live="polite">
            {loading && shops.length === 0 && <p className="empty-message">Dükkânlar yükleniyor…</p>}
            {!loading && !error && shops.length === 0 && <p className="empty-message">Eşleşen dükkân bulunamadı.</p>}
            {shops.map((shop) => {
              const startingPrice = Math.min(...shop.products.map((product) => Number(product.price)))
              return (
                <button
                  className={`shop-result${selectedShop?.id === shop.id ? ' is-selected' : ''}`}
                  key={shop.id}
                  type="button"
                  onClick={() => setSelectedShop(shop)}
                >
                  <span className="shop-result-mark"><Coffee size={17} /></span>
                  <span className="shop-result-info">
                    <strong>{shop.name.replace('KahveCell ', '')}</strong>
                    <small>{shop.address}</small>
                    <span className="shop-result-meta">
                      {shop.products.length} içecek
                      {shop.distance_km != null && ` · ${shop.distance_km.toFixed(1)} km`}
                    </span>
                  </span>
                  <span className="shop-result-price">{money.format(startingPrice)}</span>
                </button>
              )
            })}
          </div>
        </aside>
      </section>
    </div>
  )
}