import { useEffect } from 'react'
import L from 'leaflet'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'

const ANKARA_CENTER = [39.91, 32.83]

function Viewport({ shops }) {
  const map = useMap()

  useEffect(() => {
    if (!shops.length) return
    map.fitBounds(
      L.latLngBounds(shops.map((shop) => [shop.latitude, shop.longitude])),
      { padding: [40, 40], maxZoom: 12 },
    )
  }, [map, shops])

  return null
}

function shopIcon() {
  return L.divIcon({
    className: 'leaflet-shop-pin',
    html: '<span></span>',
    iconSize: [32, 38],
    iconAnchor: [16, 34],
  })
}

export default function ShopMap({ shops, onSelect }) {
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
      />
      <Viewport shops={shops} />
      {shops.map((shop) => (
        <Marker
          key={shop.id}
          position={[shop.latitude, shop.longitude]}
          icon={shopIcon()}
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
      ))}
    </MapContainer>
  )
}