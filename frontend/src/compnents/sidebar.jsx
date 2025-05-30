import React from "react";
import FolderList from "./FolderList";
import ChatList from "./chatlist";

const sidebar = () => (
  <aside style={{
    width: 320,
    background: "#23272a",
    color: "#fff",
    padding: 24,
    display: "flex",
    flexDirection: "column",
    borderRadius: 24,
    margin: 16
  }}>
    <div style={{ fontWeight: "bold", fontSize: 22, marginBottom: 24 }}>
      <span style={{ marginRight: 8 }}>🤖</span> My Chats
    </div>
    <input
      placeholder="Search"
      style={{
        background: "#181c1f",
        border: "none",
        borderRadius: 8,
        padding: "8px 12px",
        color: "#fff",
        marginBottom: 16
      }}
    />
    <FolderList />
    <ChatList />
    <button style={{
      marginTop: "auto",
      background: "#16c784",
      color: "#fff",
      border: "none",
      borderRadius: 8,
      padding: "12px 0",
      fontSize: 16,
      fontWeight: "bold",
      cursor: "pointer"
    }}>
      + New chat
    </button>
  </aside>
);

export default sidebar;
