import React from "react";

const chats = [
  {
    title: "Plan a 3-day trip",
    desc: "A 3-day trip to see the northern lights in Norway..."
  },
  {
    title: "Ideas for a customer loyalty program",
    desc: "Here are seven ideas for a customer loyalty..."
  },
  {
    title: "Help me pick",
    desc: "Here are some gift ideas for your fishing-loving..."
  }
];

const chatlist = () => (
  <div style={{ marginBottom: 24 }}>
    <div style={{ fontWeight: "bold", marginBottom: 8 }}>Chats</div>
    {chats.map(chat => (
      <div key={chat.title} style={{
        background: "#181c1f",
        borderRadius: 8,
        padding: "8px 12px",
        marginBottom: 8
      }}>
        <div style={{ fontWeight: "bold" }}>{chat.title}</div>
        <div style={{ fontSize: 13, color: "#aaa" }}>{chat.desc}</div>
      </div>
    ))}
  </div>
);

export default chatlist;
