import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowUpRight, Clock3, MapPin } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { apiRequest, ApiError } from '../api/client'

const money = new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 })

export default function ShopDetailPage() {
  const { shopId } = useParams()
  const navigate = useNavigate()
  const [shop, setShop] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    apiRequest(`/shops/${shopId}`, { auth: false })
      .then((result) => { if (active) setShop(result) })
      .catch((requestError) => { if (active) setError(requestError instanceof ApiError ? requestError.message : 'Dükkân yüklenemedi.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [shopId])

  if (loading) return <div className="page-state">Dükkân bilgileri yükleniyor…</div>
  if (error || !shop) return <div className="page-state page-error">{error || 'Dükkân bulunamadı.'}</div>

  return (
    <div className="page-stack narrow-page">
      <button className="back-button" type="button" onClick={() => navigate(-1)}><ArrowLeft size={16} /> Haritaya dön</button>
      <section className="shop-detail-hero">
        <div className="shop-detail-emblem">{shop.name.replace('KahveCell ', '').slice(0, 1)}</div>
        <div className="shop-detail-copy">
          <p className="eyebrow">KAHVECELL NOKTASI / ANKARA</p>
          <h2>{shop.name.replace('KahveCell ', '')}</h2>
          <p><MapPin size={15} />{shop.address}</p>
          <p><Clock3 size={15} />Hafta içi {shop.opening_hours?.weekdays ?? '08:00-22:00'}</p>
        </div>
        <div className="coordinate-stamp">{shop.latitude.toFixed(4)}° N<br />{shop.longitude.toFixed(4)}° E</div>
      </section>

      <section className="section-heading">
        <div><p className="eyebrow">BUGÜNÜN MENÜSÜ</p><h3>Ne içiyoruz?</h3></div>
        <span className="muted-copy">{shop.products.length} içecek</span>
      </section>

      <div className="menu-list">
        {shop.products.map((product, index) => (
          <article className="menu-item" key={product.id}>
            <span className={`menu-item-art art-${index % 4}`} aria-hidden="true">{product.name.slice(0, 1)}</span>
            <span className="menu-item-copy"><strong>{product.name}</strong><small>{product.description}</small></span>
            <strong className="menu-price">{money.format(Number(product.price))}</strong>
            <Link
              className="icon-button menu-order-link"
              to={`/shops/${shop.id}/order?productId=${product.id}`}
              aria-label={`${product.name} siparişi ver`}
              title={`${product.name} siparişi ver`}
            ><ArrowUpRight size={18} /></Link>
          </article>
        ))}
      </div>
      <Link className="button button-primary full-button" to={`/shops/${shop.id}/order`}>Bu dükkândan sipariş ver <ArrowUpRight size={17} /></Link>
    </div>
  )
}