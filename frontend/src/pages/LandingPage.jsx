import React from "react";
import { useNavigate } from "react-router-dom";

const LandingPage = () => {
  const navigate = useNavigate();
  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      background: "#111"
    }}>
      <h1 style={{ color: "#fff" }}>Welcome to My Chats</h1>
      <button
        style={{
          marginTop: 24,
          padding: "12px 32px",
          fontSize: 18,
          borderRadius: 8,
          background: "#16c784",
          color: "#fff",
          border: "none",
          cursor: "pointer"
        }}
        onClick={() => navigate("/app")}
      >
        Enter App
      </button>
    </div>
  );
};

export default LandingPage;
