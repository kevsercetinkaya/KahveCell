import { useState } from 'react'
import { ArrowLeft, ArrowRight, Coffee, ShieldCheck } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '../api/client'
import { useAuth } from '../app/useAuth'

function normalizePhoneNumber(value) {
  const digits = value.replace(/\D/g, '')
  if (digits.startsWith('90')) return `+${digits}`
  if (digits.startsWith('0')) return `+9${digits}`
  return `+90${digits}`
}

export default function AuthPage({ mode }) {
  const isRegister = mode === 'register'
  const { requestLoginCode, requestRegistrationCode, verifyCode } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [step, setStep] = useState('phone')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleRequestCode(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const normalizedPhone = normalizePhoneNumber(phone)
      const result = isRegister
        ? await requestRegistrationCode({
            phone_number: normalizedPhone,
            full_name: fullName.trim(),
            email: email.trim() || null,
          })
        : await requestLoginCode(normalizedPhone)
      setPhone(normalizedPhone)
      setNotice(result.message)
      setStep('otp')
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'İstek gönderilemedi.')
    } finally {
      setBusy(false)
    }
  }

  async function handleVerify(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await verifyCode(phone, code)
      navigate(location.state?.from ?? '/', { replace: true })
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Kod doğrulanamadı.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-brand-panel">
        <Link className="auth-brand" to="/login">
          <span className="auth-brand-mark"><Coffee size={20} /></span>
          <span>Kahve<span>Cell</span></span>
        </Link>
        <div className="auth-brand-copy">
          <p className="auth-eyebrow">ŞEHRİN RİTMİNE KARIŞ</p>
          <h1>İyi kahven,<br />yakınında.</h1>
          <p>Ankara’daki anlaşmalı kahve noktalarını keşfet, aboneliğinle sıranı beklemeden al.</p>
        </div>
        <div className="auth-brand-note"><span /> Ankara’dan, günün her anına.</div>
        <div className="auth-orbit auth-orbit-one" />
        <div className="auth-orbit auth-orbit-two" />
      </section>

      <section className="auth-form-panel">
        <div className="auth-mobile-brand">
          <span className="auth-brand-mark"><Coffee size={19} /></span>
          <strong>Kahve<span>Cell</span></strong>
        </div>
        <div className="auth-form-wrap">
          <p className="auth-form-kicker">{isRegister ? 'ARAMIZA KATIL' : 'TEKRAR HOŞ GELDİN'}</p>
          <h2>{step === 'otp' ? 'Telefonunu doğrula' : isRegister ? 'Hesabını oluştur' : 'Giriş yap'}</h2>
          <p className="auth-subtitle">
            {step === 'otp'
              ? `${phone} numarasına gönderilen kodu gir.`
              : 'Telefon numaranla güvenle devam et.'}
          </p>

          {step === 'phone' ? (
            <form className="auth-form" onSubmit={handleRequestCode}>
              {isRegister && (
                <>
                  <label className="field-label" htmlFor="full-name">Ad soyad</label>
                  <input
                    id="full-name"
                    className="text-input"
                    autoComplete="name"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    minLength={2}
                    maxLength={100}
                    required
                  />
                  <label className="field-label" htmlFor="email">E-posta <span>İsteğe bağlı</span></label>
                  <input
                    id="email"
                    className="text-input"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </>
              )}
              <label className="field-label" htmlFor="phone">GSM numarası</label>
              <div className="phone-input-wrap">
                <span>+90</span>
                <input
                  id="phone"
                  className="text-input"
                  type="tel"
                  autoComplete="tel-national"
                  inputMode="tel"
                  placeholder="5XX XXX XX XX"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  required
                />
              </div>
              <button className="button button-primary auth-submit" type="submit" disabled={busy}>
                {busy ? 'Gönderiliyor…' : 'SMS kodu gönder'} <ArrowRight size={17} />
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={handleVerify}>
              <label className="field-label" htmlFor="otp">Doğrulama kodu</label>
              <input
                id="otp"
                className="text-input otp-input"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]{4}"
                maxLength={4}
                placeholder="••••"
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 4))}
                required
              />
              {notice && <p className="auth-notice" role="status"><ShieldCheck size={16} />{notice}</p>}
              <button className="button button-primary auth-submit" type="submit" disabled={busy || code.length !== 4}>
                {busy ? 'Doğrulanıyor…' : 'Devam et'} <ArrowRight size={17} />
              </button>
              <button className="back-link" type="button" onClick={() => { setStep('phone'); setCode('') }}>
                <ArrowLeft size={15} /> Telefon numarasını değiştir
              </button>
            </form>
          )}

          {error && <p className="form-error" role="alert">{error}</p>}

          {step === 'phone' && (
            <p className="auth-switch">
              {isRegister ? 'Zaten hesabın var mı?' : 'İlk kez mi buradasın?'}{' '}
              <Link to={isRegister ? '/login' : '/register'}>{isRegister ? 'Giriş yap' : 'Kayıt ol'}</Link>
            </p>
          )}
        </div>
        <footer className="auth-legal">Devam ederek kullanım koşullarını kabul etmiş olursun.</footer>
      </section>
    </main>
  )
}