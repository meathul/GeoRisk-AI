// components/LocationPickerMap.jsx
import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Component to handle map center changes
const MapController = ({ searchLocation }) => {
  const map = useMap();

  useEffect(() => {
    if (searchLocation) {
      map.setView([searchLocation.lat, searchLocation.lng], 5);
    }
  }, [searchLocation, map]);

  return null;
};

const LocationMarker = ({ onLocationSelect, searchLocation }) => {
  const [position, setPosition] = useState(null);
  const [address, setAddress] = useState("");

  // Update marker when search location changes
  useEffect(() => {
    if (searchLocation) {
      setPosition([searchLocation.lat, searchLocation.lng]);
      setAddress(searchLocation.address);
    }
  }, [searchLocation]);

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

const LocationPickerMap = ({ onLocationSelect, searchLocation }) => (
  <MapContainer center={[39.8283, -98.5795]} zoom={4.5} style={{ height: "100%", width: "100%" }}>
    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    <LocationMarker onLocationSelect={onLocationSelect} searchLocation={searchLocation} />
    <MapController searchLocation={searchLocation} />
  </MapContainer>
);

export default LocationPickerMap;