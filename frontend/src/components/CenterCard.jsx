import React, { useState, useEffect } from "react";
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

  // Fixed bot response text
  const fixedResponse = `
High temperatures: The maximum temperature is expected to go as high as 29°C. Heavy rainfall: There is a 100% chance of precipitation, with heavy downpours and frequent lightning. High humidity: The relative humidity is expected to be around 89%. Cloudy skies: The weather forecast indicates cloudy skies with occasional rain and thunderstorms. Air quality: The current air quality index (AQI) is not available, but it is expected to be moderate to poor due to the high levels of pollution in the area. </current> <history> Increasing temperatures: The average temperature has been increasing over the past few decades, with a rise of 0.5°C to 1.5°C. Changing precipitation patterns: There has been a shift in the precipitation patterns, with more frequent and intense rainfall events. Rising sea levels: The sea level has been rising at a rate of 0.0018 m/year (1.8 mm/yr). Increased frequency of extreme weather events: There has been an increase in the frequency and intensity of extreme weather events such as floods, droughts, and heatwaves. Loss of biodiversity: The changing climate has led to a loss of biodiversity, with many species facing extinction due to habitat destruction and changing environmental conditions. </history> <future> Continued temperature rise: The temperature is expected to rise by another 1.5°C to 2.5°C by 2050. Increased precipitation: The precipitation is expected to increase by 10% to 20% by 2050. Sea level rise: The sea level is expected to rise by 0.11 m by 2050. Increased frequency of extreme weather events: The frequency and intensity of extreme weather events such as floods, droughts, and heatwaves are expected to increase. Saltwater intrusion: The rising sea level is expected to lead to saltwater intrusion into freshwater sources, affecting agriculture and human consumption. </future> <risk> High risk of flooding: The area is prone to flooding due to heavy rainfall and sea level rise. Drought risk: The area is also at risk of drought, particularly during the summer months. Heatwave risk: The area is at risk of heatwaves, particularly during the summer months. Loss of livelihoods: The changing climate is expected to affect the livelihoods of people dependent on agriculture, fishing, and other climate-sensitive sectors. Health risks: The changing climate is expected to increase the risk of water-borne and vector-borne diseases. </risk> <economy> Loss of revenue: The changing climate is expected to affect the revenue of the state, particularly in the agriculture and tourism sectors. Increased costs: The changing climate is expected to increase the costs of infrastructure, healthcare, and other services. Impact on industry: The changing climate is expected to affect the industry, particularly the manufacturing and construction sectors. Loss of property: The changing climate is expected to lead to loss of property, particularly in the coastal areas. Migration: The changing climate is expected to lead to migration, particularly of people living in low-lying areas. </economy> <summary> To mitigate the impacts of climate change in Ernakulam, Kerala, India, it is recommended to develop a climate-resilient business strategy, implement climate-resilient infrastructure and technology, promote climate-resilient agriculture and livelihoods, develop early warning systems and emergency response plans, and encourage climate-resilient entrepreneurship and innovation. The strategic mitigation framework should include short-term, medium-term, and long-term measures to address the climate risks and impacts. The implementation roadmap should include conducting climate risk assessments, developing a strategic mitigation framework, implementing mitigation measures, and monitoring and evaluating the effectiveness of the measures. The financial estimates for the mitigation measures should be in the range of ₹10 million to ₹1 billion over the next 20 years. The timeline for the implementation of the mitigation measures should be over the next 20 years, with specific milestones and targets to be achieved. </summary>
  `;

  // Auto-resize handler for the textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);

    // Auto-resize: cap at 120px height
    const textarea = e.target;
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
  };

  const sendMessage = () => {
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

    // Simulate bot response
    setTimeout(() => {
      setMessages((prev) => [...prev, { from: "bot", text: fixedResponse }]);
      setLoading(false);
      setInput("");
      // Reset textarea height after send
      const ta = document.querySelector("textarea.chat-input");
      if (ta) ta.style.height = "auto";
    }, 500);
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
              background: "#16c784",
              border: "none",
              borderRadius: 6,
              color: "#fff",
              padding: "6px 14px",
              marginLeft: 8,
              fontWeight: "bold",
              cursor: "pointer",
            }}
          >
            ▶
          </button>
        </div>
      </div>
    </div>
  );
};

export default CenterCard;
