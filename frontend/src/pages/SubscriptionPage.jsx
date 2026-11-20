import { useEffect, useState } from 'react'
import { Check, Coffee, Crown, RotateCw, ShieldCheck, Sparkles } from 'lucide-react'

import { apiRequest, ApiError } from '../api/client'

const price = new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 })

export default function SubscriptionPage() {
  const [plans, setPlans] = useState([])
  const [subscription, setSubscription] = useState(null)
  const [history, setHistory] = useState([])
  const [selectedPlan, setSelectedPlan] = useState('STARTER')
  const [cardNumber, setCardNumber] = useState('4242-4242-4242-4242')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function loadSubscription() {
    const [availablePlans, payments] = await Promise.all([
      apiRequest('/subscriptions/plans', { auth: false }),
      apiRequest('/payments/history').catch(() => []),
    ])
    setPlans(availablePlans)
    setHistory(payments)
    try {
      const active = await apiRequest('/subscriptions/me')
      setSubscription(active)
      setSelectedPlan(active.plan_type)
    } catch (requestError) {
      if (!(requestError instanceof ApiError) || requestError.status !== 404) throw requestError
      setSubscription(null)
    }
  }

  useEffect(() => {
    let active = true
    Promise.all([
      apiRequest('/subscriptions/plans', { auth: false }),
      apiRequest('/payments/history').catch(() => []),
    ])
      .then(async ([availablePlans, payments]) => {
        if (!active) return
        setPlans(availablePlans)
        setHistory(payments)
        try {
          const current = await apiRequest('/subscriptions/me')
          if (active) {
            setSubscription(current)
            setSelectedPlan(current.plan_type)
          }
        } catch (requestError) {
          if (requestError instanceof ApiError && requestError.status === 404) {
            if (active) setSubscription(null)
            return
          }
          throw requestError
        }
      })
      .catch((requestError) => { if (active) setError(requestError.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  async function submitPayment(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const result = await apiRequest(subscription ? '/subscriptions/me' : '/payments/process', {
        method: subscription ? 'PATCH' : 'POST',
        body: { subscription_plan: selectedPlan, card_number: cardNumber },
      })
      if (!result.success) {
        setError(result.message)
      } else {
        setMessage(result.message)
        await loadSubscription()
      }
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  async function cancelSubscription() {
    setBusy(true)
    setError('')
    setMessage('')
    try {
      await apiRequest('/subscriptions/me', { method: 'DELETE' })
      setSubscription(null)
      setMessage('Aboneliğin iptal edildi.')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="page-state">Abonelik bilgileri yükleniyor…</div>

  return (
    <div className="page-stack">
      <section className="section-heading subscription-heading">
        <div><p className="eyebrow">KAHVE HAKKIN</p><h2>Planını seç.</h2><p className="muted-copy">Şehrin her noktasında aynı kahve ayrıcalığı.</p></div>
        {subscription && (
          <div className="active-plan-chip"><span className="active-dot" /><span>AKTİF PLAN</span><strong>{subscription.plan_type}</strong></div>
        )}
      </section>

      {error && <p className="form-error" role="alert">{error}</p>}
      {message && <p className="inline-notice" role="status">{message}</p>}

      <div className="plan-grid">
        {plans.map((plan) => (
          <button
            className={`plan-card${selectedPlan === plan.plan_type ? ' is-selected' : ''}${subscription?.plan_type === plan.plan_type ? ' is-current' : ''}`}
            key={plan.plan_type}
            type="button"
            aria-pressed={selectedPlan === plan.plan_type}
            onClick={() => setSelectedPlan(plan.plan_type)}
          >
            <span className="plan-card-top">
              <span className={`plan-icon plan-${plan.plan_type.toLowerCase()}`}>
                {plan.plan_type === 'UNLIMITED' ? <Crown size={18} /> : <Coffee size={18} />}
              </span>
              {subscription?.plan_type === plan.plan_type && <span className="current-label">MEVCUT</span>}
            </span>
            <strong className="plan-name">{plan.plan_type}</strong>
            <span className="plan-price">{price.format(Number(plan.monthly_price))}<small> / ay</small></span>
            <span className="plan-divider" />
            <span className="plan-feature"><Check size={15} />{plan.is_unlimited ? 'Sınırsız kahve' : `${plan.coffee_credits} kahve / ay`}</span>
            <span className="plan-feature"><Check size={15} />Tüm anlaşmalı dükkânlar</span>
            {plan.guest_credits > 0 && <span className="plan-feature"><Check size={15} />{plan.guest_credits} misafir hakkı</span>}
            {plan.priority_service && <span className="plan-feature"><Sparkles size={15} />Öncelikli servis</span>}
            {selectedPlan === plan.plan_type && <span className="plan-selection"><Check size={14} /></span>}
          </button>
        ))}
      </div>

      <section className="payment-panel">
        <div className="payment-copy">
          <p className="eyebrow">PAYCELL / TEST ORTAMI</p>
          <h3>{subscription ? 'Plan değişikliğini tamamla' : 'Aboneliğini başlat'}</h3>
          <p>Simülasyon dışında kart bilgisi girme. Kart numarası sunucuda saklanmaz.</p>
        </div>
        <form className="payment-form" onSubmit={submitPayment}>
          <label className="field-label" htmlFor="test-card">Test kartı</label>
          <select id="test-card" className="text-input" value={cardNumber} onChange={(event) => setCardNumber(event.target.value)}>
            <option value="4242-4242-4242-4242">Başarılı · 4242 4242 4242 4242</option>
            <option value="4000-0000-0000-0002">Başarısız · 4000 0000 0000 0002</option>
          </select>
          <button className="button button-primary payment-submit" type="submit" disabled={busy || !selectedPlan}>
            {busy ? 'İşleniyor…' : subscription ? 'Planı değiştir' : 'Simülasyonu çalıştır'} <RotateCw size={16} />
          </button>
          {subscription && <button className="cancel-link" type="button" disabled={busy} onClick={cancelSubscription}>Aboneliği iptal et</button>}
        </form>
        <div className="payment-safety"><ShieldCheck size={15} />Kart bilgileri kayıt altına alınmaz</div>
      </section>

      <section className="history-panel">
        <div className="section-heading"><div><p className="eyebrow">SON HAREKETLER</p><h3>Ödeme geçmişi</h3></div></div>
        {history.length === 0 ? <p className="muted-copy">Henüz ödeme hareketi yok.</p> : history.slice(0, 5).map((payment) => (
          <div className="payment-history-row" key={payment.transaction_id}>
            <span>{payment.plan_type}</span>
            <strong>{price.format(Number(payment.amount))}</strong>
            <small>{payment.status === 'SUCCEEDED' ? 'Başarılı' : 'Başarısız'}</small>
            <time>{new Date(payment.created_at).toLocaleDateString('tr-TR')}</time>
          </div>
        ))}
      </section>
    </div>
  )
}