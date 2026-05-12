import { useState, useEffect } from 'react';
import { Brief } from '../types';
import { fetchBriefList, fetchBrief } from '../lib/api';
import MarkdownRenderer from './MarkdownRenderer';

export default function HistoryView() {
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [selectedBrief, setSelectedBrief] = useState<Brief | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBriefs();
  }, []);

  const loadBriefs = async () => {
    try {
      setIsLoading(true);
      const list = await fetchBriefList();
      setBriefs(list);
      if (list.length > 0) {
        handleSelect(list[0]);
      }
    } catch (err) {
      setError('Failed to load briefs');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = async (brief: Brief) => {
    try {
      // If we don't have content, fetch it
      if (!brief.content) {
        const fullBrief = await fetchBrief(brief.company);
        setSelectedBrief(fullBrief);
      } else {
        setSelectedBrief(brief);
      }
    } catch (err) {
      setError('Failed to load brief content');
    }
  };

  if (isLoading && briefs.length === 0) {
    return <div className="history-view"><div className="history-list">Loading...</div></div>;
  }

  return (
    <div className="history-view animate-fade-in">
      <div className="history-list">
        <div className="activity-header">
          <span className="activity-title">Past Briefs</span>
        </div>
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {briefs.length === 0 ? (
            <div style={{ padding: '24px', color: 'var(--text-3)' }}>No briefs found yet.</div>
          ) : (
            briefs.map((b, i) => (
              <div
                key={i}
                className={`history-item ${selectedBrief?.company === b.company ? 'active' : ''}`}
                onClick={() => handleSelect(b)}
              >
                <div className="history-company">{b.company}</div>
                <div className="history-meta">{b.filename || 'Brief'}</div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="main-content" style={{ overflowY: 'auto', padding: '60px 40px' }}>
        {selectedBrief ? (
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <MarkdownRenderer content={selectedBrief.content || ''} />
          </div>
        ) : (
          <div className="brief-empty">Select a brief to view</div>
        )}
      </div>
    </div>
  );
}
