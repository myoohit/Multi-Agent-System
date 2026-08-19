/**
 * PipelineDiagram: the 4 agent nodes connected by a "signal rail" that
 * lights up as each step completes. `steps` comes from App.jsx and looks
 * like: { search: {status, data}, reader: {...}, writer: {...}, critic: {...} }
 */
const AGENTS = [
  { key: 'search', label: 'Search Agent', desc: 'Gathers recent web information' },
  { key: 'reader', label: 'Reader Agent', desc: 'Scrapes & extracts deep content' },
  { key: 'writer', label: 'Writer Chain', desc: 'Drafts the full research report' },
  { key: 'critic', label: 'Critic Chain', desc: 'Reviews and scores the report' },
];

// Maps a status to a color, used for both the dot and the rail segment
function statusColor(status) {
  if (status === 'done') return 'var(--accent-cyan)';
  if (status === 'running') return 'var(--accent-amber)';
  return 'var(--border)'; // waiting
}

export default function PipelineDiagram({ steps }) {
  return (
    <section className="container" style={{ padding: '48px 0' }}>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 24, marginBottom: 24 }}>
        Pipeline
      </h2>

      <div style={{ position: 'relative' }}>
        {AGENTS.map((agent, i) => {
          const state = steps[agent.key];
          const isLast = i === AGENTS.length - 1;

          return (
            <div key={agent.key} style={{ position: 'relative', display: 'flex', gap: 20 }}>
              {/* Left column: numbered marker + rail segment below it.
                  Numbering is earned here — this genuinely is a fixed sequence. */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  border: `2px solid ${statusColor(state.status)}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'var(--font-mono)', fontSize: 13,
                  color: statusColor(state.status),
                  transition: 'border-color 0.4s ease, color 0.4s ease',
                  flexShrink: 0,
                }}>
                  {i + 1}
                </div>
                {!isLast && (
                  <div style={{
                    width: 2, flex: 1, minHeight: 48,
                    background: state.status === 'done' ? 'var(--accent-cyan)' : 'var(--border)',
                    transition: 'background 0.5s ease',
                  }} />
                )}
              </div>

              {/* Right column: the card itself */}
              <div style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                padding: '18px 20px',
                marginBottom: 20,
                flex: 1,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0, fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 16 }}>
                    {agent.label}
                  </h3>
                  <StatusBadge status={state.status} />
                </div>
                <p style={{ margin: '6px 0 0', color: 'var(--text-dim)', fontSize: 14 }}>
                  {agent.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function StatusBadge({ status }) {
  if (status === 'running') {
    return (
      <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent-amber)' }}>
        <span className="pulse-dot" />
        RUNNING
      </span>
    );
  }
  if (status === 'done') {
    return <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent-cyan)' }}>DONE</span>;
  }
  return <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-dim)' }}>WAITING</span>;
}