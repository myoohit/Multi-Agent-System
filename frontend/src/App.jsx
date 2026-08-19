import { useState, useRef } from 'react';
import Hero from './components/Hero';
import PipelineDiagram from './components/PipelineDiagram';
import OutputPanel from './components/OutputPanel';
import InfoSection from './components/InfoSection';
import Footer from './components/Footer';

const API_URL = import.meta.env.VITE_API_URL;

const INITIAL_STEPS = {
  search: { status: 'waiting', data: null },
  reader: { status: 'waiting', data: null },
  writer: { status: 'waiting', data: null },
  critic: { status: 'waiting', data: null },
};

export default function App() {
  const [topic, setTopic] = useState('');
  const [steps, setSteps] = useState(INITIAL_STEPS);
  const [isRunning, setIsRunning] = useState(false);
  const eventSourceRef = useRef(null); // holds the open SSE connection so we can close it

  function runPipeline(topic) {
    // Reset the board and open a fresh SSE connection to the backend.
    // EventSource handles the "data: {...}\n\n" parsing for us automatically.
    setSteps(INITIAL_STEPS);
    setIsRunning(true);

    const url = `${API_URL}/research?topic=${encodeURIComponent(topic)}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.step === 'pipeline' && payload.status === 'complete') {
        es.close();
        setIsRunning(false);
        return;
      }

      // Merge the new event into the matching step, keeping any data
      // already there if this event doesn't carry new data (e.g. "running").
      setSteps((prev) => ({
        ...prev,
        [payload.step]: {
          status: payload.status,
          data: payload.data ?? prev[payload.step].data,
        },
      }));
    };

    es.onerror = () => {
      // Something went wrong (backend down, network issue, etc.)
      es.close();
      setIsRunning(false);
    };
  }

  return (
    <div>
      <Hero topic={topic} setTopic={setTopic} onRun={runPipeline} isRunning={isRunning} />
      <PipelineDiagram steps={steps} />
      <OutputPanel steps={steps} topic={topic} />
      <InfoSection />
      <Footer />
    </div>
  );
}