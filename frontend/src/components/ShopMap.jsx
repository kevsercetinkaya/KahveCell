import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'

const ANKARA_CENTER = [39.91, 32.83]

function MapViewport({ shops, selectedShop }) {
  const map = useMap()

  useEffect(() => {
    const container = map.getContainer()
    let frameId

    const refreshMap = () => {
      frameId = window.requestAnimationFrame(() => {
        map.invalidateSize({ animate: false, pan: false })
      })
    }

    refreshMap()
    const resizeObserver = new ResizeObserver(refreshMap)
    resizeObserver.observe(container)
    window.addEventListener('resize', refreshMap)

    return () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', refreshMap)
      if (frameId) window.cancelAnimationFrame(frameId)
    }
  }, [map])

  useEffect(() => {
    if (selectedShop) return
    if (shops.length === 0) return

    map.invalidateSize({ animate: false, pan: false })
    map.fitBounds(
      L.latLngBounds(shops.map((shop) => [shop.latitude, shop.longitude])),
      { padding: [40, 40], maxZoom: 12 },
    )
  }, [map, shops, selectedShop])

  useEffect(() => {
    if (!selectedShop) return

    map.invalidateSize({ animate: false, pan: false })
    map.flyTo(
      [selectedShop.latitude, selectedShop.longitude],
      Math.max(map.getZoom(), 15),
      { animate: true, duration: 0.45 },
    )
  }, [map, selectedShop])

  return null
}

function shopIcon(isSelected = false) {
  return L.divIcon({
    className: `leaflet-shop-pin${isSelected ? ' is-selected' : ''}`,
    html: '<span></span>',
    iconSize: [32, 38],
    iconAnchor: [16, 34],
  })
}

function ShopMarker({ shop, selectedShop, onSelect }) {
  const markerRef = useRef(null)
  const isSelected = selectedShop?.id === shop.id

  useEffect(() => {
    if (isSelected) {
      window.requestAnimationFrame(() => markerRef.current?.openPopup())
    }
  }, [isSelected])

  return (
    <Marker
      ref={markerRef}
      position={[shop.latitude, shop.longitude]}
      icon={shopIcon(isSelected)}
      eventHandlers={{ click: () => onSelect?.(shop) }}
    >
      <Popup>
        <div className="map-popup">
          <strong>{shop.name.replace('KahveCell ', '')}</strong>
          <span>{shop.address}</span>
          <Link to={`/shops/${shop.id}`}>Dükkânı incele</Link>
        </div>
      </Popup>
    </Marker>
  )
}

export default function ShopMap({ shops, selectedShop, onSelect }) {
  return (
    <MapContainer
      className="leaflet-map"
      center={ANKARA_CENTER}
      zoom={11}
      minZoom={9}
      maxZoom={18}
      scrollWheelZoom={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> katkıda bulunanlar'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        updateWhenIdle
        keepBuffer={2}
      />
      <MapViewport shops={shops} selectedShop={selectedShop} />
      {shops.map((shop) => (
        <ShopMarker
          key={shop.id}
          shop={shop}
          selectedShop={selectedShop}
          onSelect={onSelect}
        />
      ))}
    </MapContainer>
  )
}