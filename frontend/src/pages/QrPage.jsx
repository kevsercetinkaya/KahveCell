import { useEffect, useState } from 'react'
import { ArrowLeft, Check, Clock3, MapPin, QrCode } from 'lucide-react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { apiRequest } from '../api/client'

const statusLabels = {
  PENDING: 'Sipariş alındı',
  ACCEPTED: 'Dükkân onayladı',
  PREPARING: 'Hazırlanıyor',
  READY: 'Teslim almaya hazır',
  DELIVERED: 'Teslim edildi',
  COMPLETED: 'Tamamlandı',
  CANCELLED: 'İptal edildi',
}

export default function QrPage() {
  const { orderId } = useParams()
  const location = useLocation()
  const [order, setOrder] = useState(location.state?.order ?? null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (order) return
    let active = true
    apiRequest(`/orders/${orderId}`)
      .then((result) => { if (active) setOrder(result) })
      .catch((requestError) => { if (active) setError(requestError.message) })
    return () => { active = false }
  }, [orderId, order])

  if (error) return <div className="page-state page-error">{error}</div>
  if (!order) return <div className="page-state">Sipariş bilgileri yükleniyor…</div>

  return (
    <div className="page-stack qr-page">
      <Link className="back-button" to="/orders"><ArrowLeft size={16} /> Siparişlerim</Link>
      <section className="qr-layout">
        <div className="qr-copy">
          <p className="eyebrow">SİPARİŞ / #{String(order.id).padStart(5, '0')}</p>
          <h2>Kahven hazır<br />olduğunda göster.</h2>
          <p className="muted-copy">Bu kod yalnızca bu sipariş için geçerlidir. Dükkân sahibi okuttuğunda imzası doğrulanır.</p>
          <div className="qr-order-meta">
            <span><MapPin size={16} />{order.shop_name}</span>
            <span><Clock3 size={16} />{statusLabels[order.status] ?? order.status}</span>
            <strong>{order.product_name} · {order.customizations?.size ?? 'M'}</strong>
          </div>
          <div className="qr-security-note"><Check size={16} />İmzalı ve sipariş kaydıyla eşleşiyor</div>
        </div>
        <div className="qr-ticket">
          <div className="qr-ticket-top"><span>KAHVECELL</span><QrCode size={18} /></div>
          <div className="qr-image-wrap">
            {order.qr_image_data
              ? <img src={order.qr_image_data} alt={`Sipariş ${order.id} için imzalı QR kodu`} />
              : <p>QR görseli yüklenemedi</p>}
          </div>
          <span className="qr-code-id">KC-{String(order.id).padStart(7, '0')}</span>
          <a className="qr-image-link" href={`http://127.0.0.1:8000/api/v1/orders/${order.id}/qr.png`} target="_blank" rel="noreferrer">QR görselini aç</a>
        </div>
      </section>
    </div>
  )
}