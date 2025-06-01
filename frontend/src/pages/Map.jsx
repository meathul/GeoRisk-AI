// pages/Map.jsx
import React, { useState } from "react";
import LocationPickerMap from "../compnents/LocationPickerMap";

const Map = () => {
  const [locationData, setLocationData] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const handleLocationSelect = (data) => {
    setLocationData(data);
    setSubmitted(false); // reset state when new location is selected
  };

  const handleSubmit = async () => {
    if (!locationData) return;

    try {
      // Send to your backend here (example URL)
      const response = await fetch("http://localhost:5000/api/locations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(locationData),
      });

      if (!response.ok) throw new Error("Failed to submit location");

      setSubmitted(true);
      console.log("Location submitted:", locationData);
    } catch (error) {
      console.error("Error submitting location:", error);
      alert("Submission failed.");
    }
  };

  return (
    <div>
      <h2 style={{ textAlign: "center" }}>Click on the Map to Select a Location</h2>
      <LocationPickerMap onLocationSelect={handleLocationSelect} />

      {locationData && (
        <div style={{ padding: "1rem", backgroundColor: "#f9f9f9" }}>
          <h3>Selected Location Details:</h3>
          <p><b>Latitude:</b> {locationData.lat}</p>
          <p><b>Longitude:</b> {locationData.lng}</p>
          <p><b>Address:</b> {locationData.address}</p>

          <button
            style={{
              marginTop: "1rem",
              padding: "10px 20px",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer"
            }}
            onClick={handleSubmit}
          >
            Submit Location
          </button>

          {submitted && <p style={{ color: "green" }}>Location submitted successfully!</p>}
        </div>
      )}
    </div>
  );
};

export default Map;
