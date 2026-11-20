import {
  Coffee,
  CreditCard,
  LogOut,
  MapPinned,
  ReceiptText,
} from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../app/useAuth'

const navigation = [
  { to: '/', label: 'Keşfet', icon: MapPinned, end: true },
  { to: '/orders', label: 'Siparişlerim', icon: ReceiptText },
  { to: '/subscription', label: 'Aboneliğim', icon: CreditCard },
]

const pageTitles = [
  [/^\/$/, 'Ankara’da kahve molası'],
  [/^\/shops\/\d+$/, 'Dükkân detayları'],
  [/^\/shops\/\d+\/order$/, 'Siparişini hazırla'],
  [/^\/orders$/, 'Sipariş geçmişim'],
  [/^\/orders\/\d+\/qr$/, 'Teslim alma kodun'],
  [/^\/subscription$/, 'Aboneliğim'],
]

export default function AppShell() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const title = pageTitles.find(([pattern]) => pattern.test(location.pathname))?.[1] ?? 'KahveCell'

  async function handleSignOut() {
    await signOut()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <NavLink className="app-brand" to="/" aria-label="KahveCell ana sayfa">
          <span className="app-brand-icon"><Coffee size={19} /></span>
          <span>Kahve<span>Cell</span></span>
        </NavLink>

        <p className="nav-caption">MENÜ</p>
        <nav className="side-nav" aria-label="Ana gezinme">
          {navigation.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-link${isActive ? ' is-active' : ''}`}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="user-chip">
            <span className="user-avatar">{user?.full_name?.slice(0, 1) ?? 'K'}</span>
            <span className="user-meta">
              <strong>{user?.full_name ?? 'KahveCell üyesi'}</strong>
              <small>{user?.phone_number}</small>
            </span>
          </div>
          <button className="signout-button" type="button" onClick={handleSignOut}>
            <LogOut size={17} /> <span>Çıkış yap</span>
          </button>
        </div>
      </aside>

      <div className="app-workspace">
        <header className="app-topbar">
          <div>
            <span className="topbar-kicker">KAHVECELL / ANKARA</span>
            <h1>{title}</h1>
          </div>
          <NavLink className="topbar-plan" to="/subscription">
            <span className="plan-spark" />
            <span>Aboneliğini gör</span>
          </NavLink>
        </header>
        <main className="page-content"><Outlet /></main>
      </div>
    </div>
  )
}