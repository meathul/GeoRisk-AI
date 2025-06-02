// pages/Map.jsx
import React, { useState } from "react";
import LocationPickerMap from "../compnents/LocationPickerMap";

const Map = ({ onSubmitLocation }) => {
  const [locationData, setLocationData] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const handleLocationSelect = (data) => {
    console.log("Selected location:", data);
    setLocationData(data);
    setSubmitted(false); // reset submit state
  };

  const handleSubmit = async () => {
    if (!locationData) return;

    try {
      const response = await fetch("http://localhost:5000/api/locations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(locationData),
      });

      if (!response.ok) throw new Error("Failed to submit location");

      setSubmitted(true);
      console.log("Location submitted:", locationData);

      // Send the data to chat as a query
      if (onSubmitLocation) {
        const { lat, lng, address } = locationData;
        const query = `Assess the climate or business risks for this location: ${address} (Latitude: ${lat}, Longitude: ${lng}).`;
        onSubmitLocation(query);
      }

    } catch (error) {
      console.error("Error submitting location:", error);
      alert("Submission failed.");
    }
  };

  return (
    <div>
      <h2 style={{ textAlign: "center", color: "white" }}>
        Click on the Map to Select a Location
      </h2>

      <LocationPickerMap onLocationSelect={handleLocationSelect} />

      {locationData && (
        <div style={{ padding: "1rem", backgroundColor: "#2b2b2b", borderRadius: "8px", marginTop: "1rem", color: "white" }}>
          <h3>Selected Location Details:</h3>
          <p><b>Latitude:</b> {locationData.lat}</p>
          <p><b>Longitude:</b> {locationData.lng}</p>
          <p><b>Address:</b> {locationData.address}</p>

          <button
            style={{
              marginTop: "1rem",
              padding: "10px 20px",
              backgroundColor: "#16c784",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer"
            }}
            onClick={handleSubmit}
          >
            Submit Location
          </button>

          {submitted && (
            <p style={{ color: "#16c784", marginTop: "0.5rem" }}>
              Location submitted successfully!
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default Map;
