import React, { useState, useEffect } from "react";
import axios from "axios";
import AgentResponse from "./AgentResponse";

const CenterCard = ({ locationAddress }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAddress, setSelectedAddress] = useState("");

  // Whenever the parent passes a new locationAddress, update selectedAddress
  useEffect(() => {
    if (locationAddress) {
      setSelectedAddress(locationAddress);
    }
  }, [locationAddress]);

  // Auto-resize handler for the textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);

    // Auto-resize: cap at 120px height
    const textarea = e.target;
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    // Format the message with location if selected
    const userMessage = selectedAddress
      ? `Location: ${selectedAddress}, Question: ${input}`
      : input;

    // Store both formatted message and original text
    setMessages((prev) => [
      ...prev,
      {
        from: "user",
        text: userMessage,
        originalInput: input,
        location: selectedAddress,
      },
    ]);
    setLoading(true);

    try {
      // Send the formatted message (with location) to backend
      const res = await axios.post("http://127.0.0.1:5000/api/chat", { 
        query: userMessage 
      });
      console.log(res.data);
      
      setMessages(msgs => [
        ...msgs, 
        { from: "bot", text: res.data.response }
      ]);
    } catch (e) {
      setMessages(msgs => [
        ...msgs, 
        { from: "bot", text: "Error connecting to server." }
      ]);
      console.log(e);
    }

    setInput("");
    setLoading(false);
    
    // Reset textarea height after send
    const ta = document.querySelector("textarea.chat-input");
    if (ta) ta.style.height = "auto";
  };

  const clearAddress = () => {
    setSelectedAddress("");
  };

  return (
    <div
      style={{
        background: "#23272a",
        borderRadius: 24,
        padding: 40,
        minWidth: "100%",
        maxWidth: "100%",
        boxShadow: "0 8px 32px rgba(0,0,0,0.25)",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        maxHeight: "100%",
        position: "relative",
      }}
    >
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 24, flexShrink: 0 }}>
        <div style={{ fontSize: 40, marginBottom: 8 }}>🤖</div>
        <div className="font-bold text-2xl text-green-400">
          Climate Risk Advisor
        </div>
      </div>

      {/* Message list (scrollable) */}
      <div
        className="chat-messages"
        style={{
          flex: 1,
          overflowY: "auto",
          marginBottom: 16,
          paddingRight: 4,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          /* Hide scrollbar in Firefox/IE */
          scrollbarWidth: "none", // Firefox
          msOverflowStyle: "none", // IE 10+
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flex: 1,
              color: "#666",
              fontSize: 14,
            }}
          >
            Start a conversation...
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {messages.map((msg, idx) => (
              <div key={idx}>
                {msg.from === "user" ? (
                  <div style={{ color: "#16c784" }}>
                    {msg.location && (
                      <div style={{ marginBottom: "4px" }}>
                        <b>Location:</b>
                        <div
                          style={{
                            paddingLeft: "10px",
                            color: "#16c784",
                          }}
                        >
                          {msg.location.split(",").map((part, idx) => (
                            <div key={idx}>{part.trim()}</div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div>
                      <b>You:</b> {msg.originalInput || msg.text}
                    </div>
                  </div>
                ) : (
                  <div>
                    <b style={{ color: "#aaa" }}>Bot:</b>
                    <AgentResponse
                      text={msg.text.replace(/<\/?current>/g, "").trim()}
                    />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div style={{ color: "#aaa" }}>
                <b>Bot:</b> Typing...
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom section (fixed) */}
      <div style={{ flexShrink: 0 }}>
        {/* Address banner */}
        {selectedAddress && (
          <div
            style={{
              background: "#181c1f",
              color: "#16c784",
              padding: "10px",
              borderRadius: "8px",
              marginBottom: "10px",
              position: "relative",
            }}
          >
            {selectedAddress.split(",").map((part, idx) => (
              <div key={idx}>{part.trim()}</div>
            ))}
            <button
              onClick={clearAddress}
              style={{
                position: "absolute",
                top: 4,
                right: 8,
                background: "transparent",
                color: "#ccc",
                border: "none",
                cursor: "pointer",
                fontSize: 16,
              }}
            >
              ❌
            </button>
          </div>
        )}

        {/* Multiline textarea input (auto‐resizing) */}
        <div
          style={{
            background: "#181c1f",
            borderRadius: 8,
            padding: "8px 12px",
            display: "flex",
            alignItems: "center",
          }}
        >
          <span style={{ marginRight: 8 }}>🌎</span>
          <textarea
            className="chat-input"
            placeholder="Type your message..."
            value={input}
            onChange={handleInputChange}
            onKeyDown={(e) => {
              // Enter without Shift → send
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            disabled={loading}
            rows={1}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              color: "#fff",
              fontSize: 16,
              outline: "none",
              resize: "none", // Prevent manual drag‐resize
              overflow: "hidden", // Hide scrollbar in textarea
              width: "100%", // Always fill full width
              lineHeight: "1.2em",
              maxHeight: "120px", // Cap at 120px height
            }}
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            style={{
              background: loading ? "#555" : "#16c784",
              border: "none",
              borderRadius: 6,
              color: "#fff",
              padding: "6px 14px",
              marginLeft: 8,
              fontWeight: "bold",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "..." : "▶"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CenterCard;