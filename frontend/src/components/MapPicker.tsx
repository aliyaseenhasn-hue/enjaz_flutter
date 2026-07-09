import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// إصلاح أيقونة marker الافتراضية
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface MapPickerProps {
  value: { lat: number; lng: number } | null;
  onChange: (location: { lat: number; lng: number }) => void;
  height?: string;
}

// مكون داخلي لالتقاط النقرات
const LocationMarker: React.FC<{
  position: { lat: number; lng: number } | null;
  onLocationChange: (pos: { lat: number; lng: number }) => void;
}> = ({ position, onLocationChange }) => {
  useMapEvents({
    click(e) {
      onLocationChange({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });

  return position ? <Marker position={[position.lat, position.lng]} /> : null;
};

// مكون لتحريك الخريطة عند تغير الموقع
const MapCenterUpdater: React.FC<{ center: { lat: number; lng: number } }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    map.setView([center.lat, center.lng], map.getZoom());
  }, [center, map]);
  return null;
};

// الوضع الافتراضي وسط بغداد
const DEFAULT_CENTER = { lat: 33.3152, lng: 44.3661 };

const MapPicker: React.FC<MapPickerProps> = ({
  value,
  onChange,
  height = '300px',
}) => {
  const center = value || DEFAULT_CENTER;

  return (
    <div style={{ height, borderRadius: '8px', overflow: 'hidden', border: '2px solid #e5e7eb' }}>
      <MapContainer
        center={[center.lat, center.lng]}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LocationMarker position={value} onLocationChange={onChange} />
        {value && <MapCenterUpdater center={value} />}
      </MapContainer>
      {value && (
        <div style={{
          padding: '6px 10px',
          background: '#f3f4f6',
          fontSize: '12px',
          color: '#6b7280',
          textAlign: 'center',
          direction: 'ltr',
        }}>
          خط العرض: {value.lat.toFixed(6)} | خط الطول: {value.lng.toFixed(6)}
        </div>
      )}
    </div>
  );
};

export default MapPicker;