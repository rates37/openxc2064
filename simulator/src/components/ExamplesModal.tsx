import React, { useState, useEffect } from 'react';
import { useSimulator } from '../SimulatorContext';

interface ExamplesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ExamplesModal: React.FC<ExamplesModalProps> = ({ isOpen, onClose }) => {
  const { importExample } = useSimulator();
  const [examples, setExamples] = useState<{ name: string; content: any }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    setLoading(true);
    setError(null);

    // Fetch the list of examples from the test_designs folder
    const fetchExamples = async () => {
      try {
        // Get the list of JSON files from the test_designs folder
        const response = await fetch('/test_designs');
        if (!response.ok) {
          throw new Error('Failed to fetch examples');
        }
        
        // Note: This assumes the server has a way to list directory contents
        // For now, we'll use a hardcoded list and try to fetch each one
        const exampleNames = [
          '8 bit counter.json',
        ];

        const loadedExamples: { name: string; content: any }[] = [];

        for (const filename of exampleNames) {
          try {
            const fileResponse = await fetch(`/test_designs/${encodeURIComponent(filename)}`);
            if (fileResponse.ok) {
              const content = await fileResponse.json();
              loadedExamples.push({
                name: filename.replace('.json', ''),
                content,
              });
            }
          } catch (e) {
            console.warn(`Failed to load example: ${filename}`, e);
          }
        }

        setExamples(loadedExamples);
        if (loadedExamples.length === 0) {
          setError('No examples found');
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load examples');
      } finally {
        setLoading(false);
      }
    };

    fetchExamples();
  }, [isOpen]);

  const loadExample = (example: { name: string; content: any }) => {
    try {
      importExample(example.content);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load example');
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 2000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          maxWidth: '400px',
          width: '90%',
          maxHeight: '600px',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
          Load Example
        </h2>

        {loading && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
            Loading examples...
          </div>
        )}

        {error && (
          <div
            style={{
              padding: '12px',
              backgroundColor: '#fee',
              color: '#c33',
              borderRadius: '4px',
              marginBottom: '16px',
              fontSize: '13px',
            }}
          >
            {error}
          </div>
        )}

        {!loading && examples.length > 0 && (
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              marginBottom: '16px',
              border: '1px solid #ddd',
              borderRadius: '4px',
            }}
          >
            {examples.map((example, index) => (
              <button
                key={index}
                onClick={() => loadExample(example)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  textAlign: 'left',
                  border: 'none',
                  borderBottom: index < examples.length - 1 ? '1px solid #eee' : 'none',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  fontSize: '14px',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget).style.backgroundColor = '#f5f5f5';
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget).style.backgroundColor = 'transparent';
                }}
              >
                {example.name}
              </button>
            ))}
          </div>
        )}

        {!loading && examples.length === 0 && !error && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
            No examples available
          </div>
        )}

        <button
          onClick={onClose}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f0f0f0',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default ExamplesModal;
