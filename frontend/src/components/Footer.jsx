export default function Footer() {
  return (
    <footer className="container" style={{
      padding: '32px 0 48px',
      borderTop: '1px solid var(--border)',
      color: 'var(--text-dim)',
      fontSize: 13,
      fontFamily: 'var(--font-mono)',
    }}>
      Built on LangChain + Groq · FastAPI · React
    </footer>
  );
}