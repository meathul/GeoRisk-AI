// pages/MainPage.jsx or index.jsx
import React, { useState } from "react";
import CenterCard from "../compnents/CenterCard"; // fix typo if needed
import Map from "./Map"; // assumes Map accepts onSubmitLocation prop

const MainPage = () => {
  const [locationQuery, setLocationQuery] = useState(null);

  // Called when Map selects a location to be sent to chat
  const handleLocationQuery = (query) => {
    setLocationQuery(query);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        gap: "40px",
        padding: "40px",
        backgroundColor: "#1e1e1e",
        minHeight: "100vh",
        color: "white",
        overflow: "hidden"
      }}
    >
      {/* Chat Panel */}
      <div style={{ flex: "0 0 500px", display: "flex", justifyContent: "center" }}>
        <CenterCard externalQuery={locationQuery} />
      </div>

      {/* Map Panel */}
      <div style={{ flex: 1 }}>
        <Map onSubmitLocation={handleLocationQuery} />
      </div>
    </div>
  );
};

export default MainPage;
