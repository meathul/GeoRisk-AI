import React from "react";
import Sidebar from "../components/sidebar";
import CenterCard from "../components/CenterCard";

const MainAppPage = () => {
  return (
    <div style={{
      minHeight: "100vh",
      background: "radial-gradient(circle at 70% 30%, #1a2a1a 0%, #111 100%)",
      display: "flex"
    }}>
      <Sidebar />
      <main style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}>
        <CenterCard />
      </main>
    </div>
  );
};

export default MainAppPage;
