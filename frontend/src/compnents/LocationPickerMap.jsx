// components/LocationPickerMap.jsx
import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const LocationMarker = ({ onLocationSelect }) => {
  const [position, setPosition] = useState(null);
  const [address, setAddress] = useState("");

  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      setPosition([lat, lng]);

      fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`)
        .then(res => res.json())
        .then(data => {
          const locationData = {
            lat,
            lng,
            address: data.display_name || "Unknown location",
            full: data,
          };
          setAddress(locationData.address);
          onLocationSelect(locationData);
        })
        .catch(console.error);
    },
  });

  return position ? (
    <Marker position={position}>
      <Popup>
        <b>Coordinates:</b> {position[0].toFixed(5)}, {position[1].toFixed(5)}<br />
        <b>Address:</b> {address}
      </Popup>
    </Marker>
  ) : null;
};

const LocationPickerMap = ({ onLocationSelect }) => (
  <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ height: "100vh", width: "100%" }}>
    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    <LocationMarker onLocationSelect={onLocationSelect} />
  </MapContainer>
);

export default LocationPickerMap;
