import ReactMarkdown from 'react-markdown';

/**
 * OutputPanel: raw search/scrape data is tucked into quiet, collapsed
 * accordions (it's supporting evidence). The report and critique are
 * the actual deliverable — rendered as real formatted markdown, given
 * visual priority and room to breathe.
 */
export default function OutputPanel({ steps }) {
  const hasRawData = steps.search.data || steps.reader.data;
  const hasReport = steps.writer.data;
  const hasCritique = steps.critic.data;

  if (!hasRawData && !hasReport) return null;

  return (
    <section className="container" style={{ padding: '16px 0 64px' }}>

      {/* --- Quiet, collapsed raw data --- */}
      {steps.search.data && (
        <RawAccordion label="Search results (raw)" content={steps.search.data} />
      )}
      {steps.reader.data && (
        <RawAccordion label="Scraped content (raw)" content={steps.reader.data} />
      )}

      {/* --- The actual report: full width, real typography --- */}
      {hasReport && (
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '32px 36px',
          marginTop: 24,
        }}>
          <p style={{
            fontFamily: 'var(--font-mono)', fontSize: 12,
            color: 'var(--accent-cyan)', textTransform: 'uppercase',
            letterSpacing: '0.05em', margin: '0 0 16px',
          }}>
            Final Research Report
          </p>
          <div className="prose">
            <ReactMarkdown>{steps.writer.data}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* --- Critique: same treatment, slightly quieter framing --- */}
      {hasCritique && (
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '28px 36px',
          marginTop: 16,
        }}>
          <p style={{
            fontFamily: 'var(--font-mono)', fontSize: 12,
            color: 'var(--accent-amber)', textTransform: 'uppercase',
            letterSpacing: '0.05em', margin: '0 0 16px',
          }}>
            Critic's Review
          </p>
          <div className="prose">
            <ReactMarkdown>{steps.critic.data}</ReactMarkdown>
          </div>
        </div>
      )}
    </section>
  );
}

/** A collapsed-by-default <details> block for raw agent output. */
function RawAccordion({ label, content }) {
  return (
    <details className="raw-accordion" style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      marginBottom: 12,
    }}>
      <summary>▸ {label}</summary>
      <pre>{content}</pre>
    </details>
  );
}