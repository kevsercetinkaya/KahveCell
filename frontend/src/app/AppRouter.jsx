import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'

import AuthProvider from './AuthProvider'
import { useAuth } from './useAuth'
import AppShell from '../components/AppShell'
import AuthPage from '../pages/AuthPage'
import HomePage from '../pages/HomePage'
import OrderPage from '../pages/OrderPage'
import OrdersPage from '../pages/OrdersPage'
import QrPage from '../pages/QrPage'
import ShopDetailPage from '../pages/ShopDetailPage'
import SubscriptionPage from '../pages/SubscriptionPage'
import '../app/app.css'

function RequireAuth() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div className="screen-state">Oturum kontrol ediliyor…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

function PublicAuthPage({ mode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="screen-state">Oturum kontrol ediliyor…</div>
  if (user) return <Navigate to="/" replace />
  return <AuthPage mode={mode} />
}

export default function AppRouter() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicAuthPage mode="login" />} />
          <Route path="/register" element={<PublicAuthPage mode="register" />} />
          <Route element={<RequireAuth />}>
            <Route element={<AppShell />}>
              <Route index element={<HomePage />} />
              <Route path="shops/:shopId" element={<ShopDetailPage />} />
              <Route path="shops/:shopId/order" element={<OrderPage />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="orders/:orderId/qr" element={<QrPage />} />
              <Route path="subscription" element={<SubscriptionPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}