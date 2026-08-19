import ReactMarkdown from 'react-markdown';

/**
 * OutputPanel: raw search/scrape data is tucked into quiet, collapsed
 * accordions (it's supporting evidence). The report and critique are
 * the actual deliverable — rendered as real formatted markdown, given
 * visual priority and room to breathe. The report also gets a
 * Download PDF button that asks the backend to typeset a clean,
 * research-paper-style PDF version.
 */
export default function OutputPanel({ steps, topic }) {
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
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
            flexWrap: 'wrap',
            gap: 12,
          }}>
            <p style={{
              fontFamily: 'var(--font-mono)', fontSize: 12,
              color: 'var(--accent-cyan)', textTransform: 'uppercase',
              letterSpacing: '0.05em', margin: 0,
            }}>
              Final Research Report
            </p>
            <DownloadButton
              topic={topic}
              report={steps.writer.data}
              critique={steps.critic.data}
            />
          </div>
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

/**
 * Download PDF button. Sends the topic + report + critique to the
 * backend's /download-pdf endpoint, which returns actual PDF bytes,
 * then triggers a browser download of that response.
 */
function DownloadButton({ topic, report, critique }) {
  async function handleDownload() {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/download-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, report, critique }),
      });

      if (!res.ok) {
        alert('Could not generate the PDF — try again.');
        return;
      }

      // Turn the PDF response into a real file download
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${(topic || 'research').trim().replace(/\s+/g, '_')}_report.pdf`;
      link.click();
      URL.revokeObjectURL(url); // free the memory once the download starts
    } catch (err) {
      alert('Something went wrong generating the PDF.');
    }
  }

  return (
    <button
      onClick={handleDownload}
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        background: 'transparent',
        border: '1px solid var(--accent-violet)',
        color: 'var(--accent-violet)',
        borderRadius: 6,
        padding: '6px 12px',
        cursor: 'pointer',
        transition: 'background 0.15s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(140, 124, 255, 0.1)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      ↓ Download PDF
    </button>
  );
}