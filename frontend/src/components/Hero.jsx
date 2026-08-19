/**
 * Hero: headline, one-line explanation, and the topic input + Run button.
 * This is the first thing visitors see — the "demo" isn't buried below.
 */
export default function Hero({ topic, setTopic, onRun, isRunning }) {
  function handleSubmit(e) {
    e.preventDefault(); // stop the page from reloading on submit
    if (topic.trim() && !isRunning) {
      onRun(topic.trim());
    }
  }

  return (
    <section style={{ padding: '80px 0 48px' }} className="container">
      <p style={{
        fontFamily: 'var(--font-mono)',
        color: 'var(--accent-cyan)',
        fontSize: 14,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        marginBottom: 16,
      }}>
        Autonomous Research Pipeline
      </p>

      <h1 style={{
        fontFamily: 'var(--font-display)',
        fontWeight: 600,
        fontSize: 'clamp(2.2rem, 5vw, 3.4rem)',
        lineHeight: 1.1,
        margin: '0 0 20px',
      }}>
        Four agents.<br />One research report.
      </h1>

      <p style={{ color: 'var(--text-dim)', fontSize: 18, maxWidth: 560, marginBottom: 40 }}>
        Give it a topic. Watch a search agent, a reader agent, a writer, and a
        critic hand work off to each other in real time — not a spinner, the
        actual pipeline.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 12, maxWidth: 560 }}>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. quantum computing in 2026"
          disabled={isRunning}
          style={{
            flex: 1,
            padding: '14px 16px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            color: 'var(--text)',
            fontFamily: 'var(--font-mono)',
            fontSize: 15,
          }}
        />
        <button
          type="submit"
          disabled={isRunning}
          style={{
            padding: '14px 24px',
            background: isRunning ? 'var(--border)' : 'var(--accent-violet)',
            color: isRunning ? 'var(--text-dim)' : '#0A0D12',
            border: 'none',
            borderRadius: 'var(--radius)',
            fontWeight: 600,
            cursor: isRunning ? 'not-allowed' : 'pointer',
            transition: 'transform 0.15s ease',
          }}
          onMouseDown={(e) => { if (!isRunning) e.currentTarget.style.transform = 'scale(0.97)'; }}
          onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          {isRunning ? 'Running…' : 'Run'}
        </button>
      </form>
    </section>
  );
}