export default function StatusCard({ title, data }) {
  return (
    <div
      style={{
        border: "1px solid #333",
        padding: 16,
        borderRadius: 8,
        minWidth: 200,
      }}
    >
      <h2>{title}</h2>
      <pre style={{ fontSize: 12 }}>
        {data ? JSON.stringify(data, null, 2) : "loading..."}
      </pre>
    </div>
  );
}
