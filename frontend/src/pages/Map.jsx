// pages/Map.jsx
import React, { useState } from "react";
import LocationPickerMap from "../components/LocationPickerMap";

const Map = ({ onSubmitLocation }) => {
  const [locationData, setLocationData] = useState(null);
  const [searchLocation, setSearchLocation] = useState(null);

  const handleLocationSelect = (data) => {
    setLocationData(data);

    // Immediately send only the address string up to the parent
    if (onSubmitLocation) {
      onSubmitLocation(data.address);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`
      );
      const results = await response.json();

      if (results && results.length > 0) {
        const result = results[0];
        const searchData = {
          lat: parseFloat(result.lat),
          lng: parseFloat(result.lon),
          address: result.display_name,
          full: result,
        };
        
        setSearchLocation(searchData);
        setLocationData(searchData);
        
        // Send the search result to parent
        if (onSubmitLocation) {
          onSubmitLocation(searchData.address);
        }
      }
    } catch (error) {
      console.error("Search error:", error);
    }
  };

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        paddingTop: "10px",
        paddingBottom: "10px",
      }}
    >
      {/* Map Container */}
      <div
        style={{
          flex: 1,
          backgroundColor: "#2b2b2b",
          borderRadius: "16px",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: "0 8px 32px rgba(0,0,0,0.25)",
        }}
      >
        <h2 
          style={{ 
            textAlign: "center", 
            color: "white", 
            margin: "0 0 20px 0",
            fontSize: "24px",
          }}
        >
          Click on the Map to Select a Location
        </h2>

        {/* Search Bar */}
        <div
          style={{
            marginBottom: "16px",
            display: "flex",
            gap: "8px",
          }}
        >
          <input
            type="text"
            placeholder="Search for a location..."
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: "8px",
              border: "1px solid #444",
              backgroundColor: "#1e1e1e",
              color: "white",
              fontSize: "16px",
              outline: "none",
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch(e.target.value);
              }
            }}
          />
          <button
            onClick={() => {
              const input = document.querySelector('input[type="text"]');
              handleSearch(input.value);
            }}
            style={{
              padding: "12px 20px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#16c784",
              color: "white",
              fontSize: "16px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Search
          </button>
        </div>

        {/* Map Component Container */}
        <div
          style={{
            flex: 1,
            borderRadius: "12px",
            overflow: "hidden",
            minHeight: 0, // Important for flex child to shrink
          }}
        >
          <LocationPickerMap 
            onLocationSelect={handleLocationSelect} 
            searchLocation={searchLocation}
          />
        </div>


      </div>
    </div>
  );
};

export default Map;