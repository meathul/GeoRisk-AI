import React from "react";

const folders = [
  "Work chats",
  "Life chats",
  "Projects chats",
  "Clients chats"
];

const FolderList = () => (
  <div style={{ marginBottom: 24 }}>
    <div style={{ fontWeight: "bold", marginBottom: 8 }}>Folders</div>
    {folders.map(folder => (
      <div key={folder} style={{
        display: "flex",
        alignItems: "center",
        background: "#181c1f",
        borderRadius: 8,
        padding: "8px 12px",
        marginBottom: 8,
        borderLeft: "4px solid #16c784"
      }}>
        <span>{folder}</span>
      </div>
    ))}
  </div>
);

export default FolderList;
