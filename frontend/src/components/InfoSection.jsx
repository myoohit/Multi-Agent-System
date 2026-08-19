const INFO = [
  { title: 'Search Agent', body: 'Runs one live web search on your topic and returns titles, URLs, and snippets — it never answers from memory.' },
  { title: 'Reader Agent', body: 'Picks the most relevant URL from the search results and scrapes it for deeper, fuller text.' },
  { title: 'Writer Chain', body: 'Combines both outputs into a structured report: introduction, key findings, conclusion, sources.' },
  { title: 'Critic Chain', body: 'Reviews the finished report and scores it out of 10, with concrete strengths and areas to improve.' },
];

export default function InfoSection() {
  return (
    <section className="container" style={{ padding: '48px 0', borderTop: '1px solid var(--border)' }}>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 24, marginBottom: 24 }}>
        How it works
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 24 }}>
        {INFO.map((item) => (
          <div key={item.title}>
            <h4 style={{ fontFamily: 'var(--font-body)', fontSize: 15, fontWeight: 600, margin: '0 0 6px', color: 'var(--accent-violet)' }}>
              {item.title}
            </h4>
            <p style={{ color: 'var(--text-dim)', fontSize: 14, lineHeight: 1.6, margin: 0 }}>
              {item.body}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}