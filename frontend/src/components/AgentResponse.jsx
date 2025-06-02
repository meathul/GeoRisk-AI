import React from "react";
import ReactMarkdown from "react-markdown";
function parseTaggedResponse(text) {
  const tags = ['history', 'future', 'risk', 'economy', 'summary', 'hello', 'bye'];
  const result = {};

  tags.forEach(tag => {
    const regex = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, 'i');
    const match = text.match(regex);
    if (match) {
      result[tag] = match[1].trim();
    }
  });

  const firstTagIndex = text.search(/<\w+>/);
  if (firstTagIndex > 0) {
    result['current'] = text.slice(0, firstTagIndex).trim();
  }

  return result;
}

const Section = ({ title, content, borderColor }) => (
  <div
    style={{
      background: "#1e1f24",
      borderLeft: `4px solid ${borderColor}`,
      padding: "16px 20px",
      marginBottom: 16,
      borderRadius: 8,
      boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
    }}
  >
    <h3 style={{ margin: 0, fontSize: 16, color: "#f0f0f0" }}>{title}</h3>
    <ReactMarkdown
  components={{
    p: ({ node, ...props }) => (
      <p style={{ marginTop: 8, fontSize: 14, color: "#cccccc", whiteSpace: "pre-wrap" }} {...props} />
    ),
  }}
>
  {content}
</ReactMarkdown>

  </div>
);

const AgentResponse = ({ text }) => {
  const data = parseTaggedResponse(text);

  if (data.hello)
    return <div style={{ fontSize: 16, color: "#16c784" }}>{data.hello}</div>;
  if (data.bye)
    return <div style={{ fontSize: 16, color: "#aaa" }}>{data.bye}</div>;

  return (
    <div>
      {data.current && (
        <Section
          title="Current Conditions"
          content={data.current}
          borderColor="#2ecc71"
        />
      )}
      {data.history && (
        <Section
          title="Historical Trends"
          content={data.history}
          borderColor="#3498db"
        />
      )}
      {data.future && (
        <Section
          title="Future Predictions"
          content={data.future}
          borderColor="#9b59b6"
        />
      )}
      {data.risk && (
        <Section
          title="Risk Assessment"
          content={data.risk}
          borderColor="#e67e22"
        />
      )}
      {data.economy && (
        <Section
          title="Economic Impact"
          content={data.economy}
          borderColor="#f1c40f"
        />
      )}
      {data.summary && (
        <Section
          title="Recommendations"
          content={data.summary}
          borderColor="#1abc9c"
        />
      )}
    </div>
  );
};

export default AgentResponse;
// This component takes a response text from an agent and parses it for specific tagged sections.