import { useEffect, useState } from 'react'
import { ArrowUpRight, Clock3, MapPin, ReceiptText } from 'lucide-react'
import { Link } from 'react-router-dom'

import { apiRequest } from '../api/client'

const statusLabels = {
  PENDING: 'Alındı', ACCEPTED: 'Onaylandı', PREPARING: 'Hazırlanıyor',
  READY: 'Hazır', DELIVERED: 'Teslim edildi', COMPLETED: 'Tamamlandı', CANCELLED: 'İptal edildi',
}

export default function OrdersPage() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    apiRequest('/orders/history')
      .then((result) => { if (active) setOrders(result) })
      .catch((requestError) => { if (active) setError(requestError.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  return (
    <div className="page-stack">
      <section className="section-heading orders-heading">
        <div><p className="eyebrow">GEÇMİŞİN</p><h2>Siparişlerim</h2></div>
        <span className="count-pill">{orders.length} sipariş</span>
      </section>
      {loading && <div className="page-state">Siparişler yükleniyor…</div>}
      {error && <div className="order-error" role="alert">{error}</div>}
      {!loading && !error && orders.length === 0 && (
        <section className="empty-panel">
          <span className="empty-icon"><ReceiptText size={23} /></span>
          <h3>Henüz siparişin yok</h3>
          <p>Haritadan yakınındaki kahve noktalarını keşfet.</p>
          <Link className="button button-primary" to="/">Dükkânları keşfet</Link>
        </section>
      )}
      <div className="orders-list">
        {orders.map((order) => (
          <article className="order-card" key={order.id}>
            <span className="order-card-icon"><ReceiptText size={19} /></span>
            <div className="order-card-main">
              <div className="order-card-title"><strong>{order.product_name}</strong><span>#{String(order.id).padStart(5, '0')}</span></div>
              <p><MapPin size={14} />{order.shop_name}</p>
              <small><Clock3 size={13} />{new Date(order.created_at).toLocaleString('tr-TR')}</small>
            </div>
            <span className={`status-pill status-${order.status.toLowerCase()}`}>{statusLabels[order.status] ?? order.status}</span>
            <Link className="icon-button" to={`/orders/${order.id}/qr`} aria-label="Sipariş QR kodunu aç"><ArrowUpRight size={18} /></Link>
          </article>
        ))}
      </div>
    </div>
  )
}