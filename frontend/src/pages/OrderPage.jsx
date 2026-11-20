import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, Coffee, Minus, Plus } from 'lucide-react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { apiRequest, ApiError } from '../api/client'

export default function OrderPage() {
  const { shopId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [shop, setShop] = useState(null)
  const [productId, setProductId] = useState(searchParams.get('productId') ?? '')
  const [size, setSize] = useState('M')
  const [sugarLevel, setSugarLevel] = useState(0)
  const [milkPreference, setMilkPreference] = useState('normal')
  const [extraShots, setExtraShots] = useState(0)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    apiRequest(`/shops/${shopId}`, { auth: false })
      .then((result) => {
        if (!active) return
        setShop(result)
        if (!productId && result.products.length) setProductId(String(result.products[0].id))
      })
      .catch(() => { if (active) setError('Dükkân bilgisi alınamadı.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [shopId, productId])

  const selectedProduct = shop?.products.find((product) => String(product.id) === String(productId))

  async function submitOrder(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const order = await apiRequest('/orders', {
        method: 'POST',
        body: {
          shop_id: Number(shopId),
          product_id: Number(productId),
          size,
          sugar_level: sugarLevel,
          milk_preference: milkPreference || null,
          extra_shots: extraShots,
        },
      })
      navigate(`/orders/${order.id}/qr`, { state: { order } })
    } catch (requestError) {
      const message = requestError instanceof ApiError ? requestError.message : 'Sipariş oluşturulamadı.'
      setError(message)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="page-state">Sipariş ekranı hazırlanıyor…</div>
  if (!shop) return <div className="page-state page-error">{error || 'Dükkân bulunamadı.'}</div>

  return (
    <div className="page-stack narrow-page">
      <Link className="back-button" to={`/shops/${shop.id}`}><ArrowLeft size={16} /> {shop.name.replace('KahveCell ', '')}</Link>
      <section className="order-intro">
        <p className="eyebrow">KAHVE MOLASI / 01</p>
        <h2>Sana göre hazırlansın.</h2>
        <p>{shop.address}</p>
      </section>

      <form className="order-form" onSubmit={submitOrder}>
        <label className="field-label" htmlFor="order-product">İçeceğini seç</label>
        <select id="order-product" className="text-input" value={productId} onChange={(event) => setProductId(event.target.value)}>
          {shop.products.map((product) => <option key={product.id} value={product.id}>{product.name} · ₺{Number(product.price).toFixed(0)}</option>)}
        </select>

        <div className="form-section-title"><span>01</span><strong>Boyut</strong></div>
        <div className="segmented-control" role="group" aria-label="Kahve boyutu">
          {['S', 'M', 'L'].map((option) => (
            <button key={option} className={size === option ? 'is-selected' : ''} type="button" onClick={() => setSize(option)}>
              <span>{option}</span><small>{option === 'S' ? 'Küçük' : option === 'M' ? 'Orta' : 'Büyük'}</small>
            </button>
          ))}
        </div>

        <div className="form-section-title"><span>02</span><strong>Şeker</strong><small>Şeker seviyesi</small></div>
        <div className="stepper-row">
          <span>{sugarLevel === 0 ? 'Şekersiz' : `${sugarLevel} küp`}</span>
          <div className="stepper">
            <button type="button" aria-label="Şekeri azalt" disabled={sugarLevel === 0} onClick={() => setSugarLevel((value) => Math.max(0, value - 1))}><Minus size={15} /></button>
            <strong>{sugarLevel}</strong>
            <button type="button" aria-label="Şekeri artır" disabled={sugarLevel === 5} onClick={() => setSugarLevel((value) => Math.min(5, value + 1))}><Plus size={15} /></button>
          </div>
        </div>

        <label className="field-label" htmlFor="milk">Süt tercihi</label>
        <select id="milk" className="text-input" value={milkPreference} onChange={(event) => setMilkPreference(event.target.value)}>
          <option value="normal">Normal süt</option>
          <option value="laktozsuz">Laktozsuz</option>
          <option value="yulaf">Yulaf sütü</option>
          <option value="none">Sütsüz</option>
        </select>

        <div className="form-section-title"><span>03</span><strong>Ekstra shot</strong></div>
        <div className="stepper-row">
          <span>Espresso shot ekle</span>
          <div className="stepper">
            <button type="button" aria-label="Shot azalt" disabled={extraShots === 0} onClick={() => setExtraShots((value) => Math.max(0, value - 1))}><Minus size={15} /></button>
            <strong>{extraShots}</strong>
            <button type="button" aria-label="Shot artır" disabled={extraShots === 3} onClick={() => setExtraShots((value) => Math.min(3, value + 1))}><Plus size={15} /></button>
          </div>
        </div>

        {error && (
          <div className="order-error" role="alert">
            <p>{error}</p>
            {error.toLocaleLowerCase('tr-TR').includes('abonelik') || error.toLocaleLowerCase('tr-TR').includes('hakkı')
              ? <Link to="/subscription">Aboneliğimi gör</Link>
              : null}
          </div>
        )}

        <div className="order-submit-row">
          <span><Coffee size={17} /> 1 abonelik hakkı</span>
          <button className="button button-primary" type="submit" disabled={busy || !selectedProduct}>
            {busy ? 'Hazırlanıyor…' : 'Siparişi ver'} <ArrowRight size={17} />
          </button>
        </div>
      </form>
    </div>
  )
}