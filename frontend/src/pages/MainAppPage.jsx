// pages/MainAppPage.jsx
import React, { useState } from "react";
import CenterCard from "../components/CenterCard";
import Map from "./Map";

const MainAppPage = () => {
  const [addressString, setAddressString] = useState("");

  // Receive address directly (no submit button)
  const handleLocationAddress = (address) => {
    setAddressString(address);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        gap: "20px",
        padding: "20px",
        backgroundColor: "#1e1e1e",
        height: "100vh",
        color: "white",
        overflow: "hidden",
      }}
    >
      {/* Chat Panel - Takes up almost half the screen */}
      <div
        style={{
          flex: "0 0 48%",        // Fixed width at 48% of screen
          display: "flex",
          justifyContent: "center",
          height: "calc(100vh - 40px)",  // Full height minus padding
        }}
      >
        <CenterCard locationAddress={addressString} />
      </div>

      {/* Map Panel - Takes up the other half */}
      <div 
        style={{ 
          flex: "0 0 48%",        // Fixed width at 48% of screen
          height: "calc(100vh - 40px)",  // Full height minus padding
        }}
      >
        <Map onSubmitLocation={handleLocationAddress} />
      </div>
    </div>
  );
};

export default MainAppPage;