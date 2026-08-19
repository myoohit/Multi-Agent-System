/**
 * OutputPanel: shows each step's raw output as soon as it arrives.
 * A step only renders once its data has come in — nothing appears
 * "empty" or as a placeholder, it just grows as the pipeline runs.
 */
const LABELS = {
  search: 'Search results',
  reader: 'Scraped content',
  writer: 'Research report',
  critic: "Critic's review",
};

export default function OutputPanel({ steps }) {
  const completedSteps = Object.entries(steps).filter(([, s]) => s.data);

  if (completedSteps.length === 0) return null;

  return (
    <section className="container" style={{ padding: '16px 0 64px' }}>
      {completedSteps.map(([key, s]) => (
        <div key={key} style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: 20,
          marginBottom: 16,
        }}>
          <h4 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--accent-cyan)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            margin: '0 0 12px',
          }}>
            {LABELS[key]}
          </h4>
          <pre style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13.5,
            color: 'var(--text)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            margin: 0,
            maxHeight: key === 'writer' ? 'none' : 260,
            overflowY: key === 'writer' ? 'visible' : 'auto',
          }}>
            {s.data}
          </pre>
        </div>
      ))}
    </section>
  );
}