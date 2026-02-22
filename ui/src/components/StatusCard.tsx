type StatusCardProps = {
  title: string;
  data: unknown;
};

export default function StatusCard({ title, data }: StatusCardProps) {
  return (
    <div
      style={{
        border: '1px solid #1a3a4a',
        padding: '12px 16px',
        borderRadius: 10,
        minWidth: 220,
        maxWidth: 300,
        background: 'rgba(8,14,22,0.92)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 0 18px rgba(0,255,255,0.06)',
      }}
    >
      <h3 style={{
        fontSize: 11, fontWeight: 600, letterSpacing: '1.5px',
        color: '#00ffff', textTransform: 'uppercase' as const,
        marginBottom: 8, borderBottom: '1px solid #152030', paddingBottom: 6,
      }}>{title}</h3>
      <pre style={{
        fontSize: 11, lineHeight: 1.45, color: '#7090a0',
        whiteSpace: 'pre-wrap', wordBreak: 'break-all',
        maxHeight: 140, overflowY: 'auto', margin: 0,
      }}>
        {data ? JSON.stringify(data, null, 2) : 'awaiting…'}
      </pre>
    </div>
  );
}
