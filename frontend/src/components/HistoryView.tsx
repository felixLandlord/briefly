import { useState, useEffect, useMemo } from 'react';
import { Brief } from '../types';
import { fetchBriefList, fetchBrief } from '../lib/api';
import MarkdownRenderer from './MarkdownRenderer';

export default function HistoryView() {
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [selectedBrief, setSelectedBrief] = useState<Brief | null>(null);
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());
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
        // Automatically select the first brief of the first company
        handleSelect(list[0]);
        setExpandedCompanies(new Set([list[0].company]));
      }
    } catch (err) {
      setError('Failed to load briefs');
    } finally {
      setIsLoading(false);
    }
  };

  const groupedBriefs = useMemo(() => {
    return briefs.reduce((acc, brief) => {
      if (!acc[brief.company]) acc[brief.company] = [];
      acc[brief.company].push(brief);
      return acc;
    }, {} as Record<string, Brief[]>);
  }, [briefs]);

  const toggleCompany = (company: string) => {
    setExpandedCompanies((prev) => {
      const next = new Set(prev);
      if (next.has(company)) next.delete(company);
      else next.add(company);
      return next;
    });
  };

  const handleSelect = async (brief: Brief) => {
    try {
      let currentBrief = brief;
      // If we don't have content, fetch it
      if (!brief.content) {
        const fullBrief = await fetchBrief(brief.company, brief.filename);
        currentBrief = { ...brief, ...fullBrief };
        
        // Sync back to the main list so we don't fetch it again
        setBriefs(prev => prev.map(b => b.path === brief.path ? currentBrief : b));
      }
      setSelectedBrief(currentBrief);
    } catch (err) {
      setError('Failed to load brief content');
    }
  };

  if (isLoading && briefs.length === 0) {
    return (
      <div className="history-view">
        <div className="history-list">
          <div className="activity-header">
            <span className="activity-title">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="history-view animate-fade-in">
      <div className="history-list">
        <div className="activity-header">
          <span className="activity-title">Brief Library</span>
        </div>
        <div style={{ overflowY: 'auto', flex: 1, padding: '8px 0' }}>
          {Object.entries(groupedBriefs).length === 0 ? (
            <div style={{ padding: '24px', color: 'var(--text-3)', fontSize: '13px' }}>
              No briefs found yet.
            </div>
          ) : (
            Object.entries(groupedBriefs).map(([company, versions]) => (
              <div key={company}>
                <div
                  className={`history-item ${expandedCompanies.has(company) ? 'expanded' : ''}`}
                  onClick={() => toggleCompany(company)}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <span style={{ 
                    fontSize: '10px', 
                    transition: 'transform 0.2s',
                    transform: expandedCompanies.has(company) ? 'rotate(90deg)' : 'none',
                    color: 'var(--text-3)'
                  }}>
                    ▶
                  </span>
                  <div className="history-company" style={{ margin: 0, fontSize: '13px' }}>{company}</div>
                  <span style={{ marginLeft: 'auto', fontSize: '10px', color: 'var(--text-4)' }}>
                    {versions.length}
                  </span>
                </div>
                
                {expandedCompanies.has(company) && (
                  <div style={{ background: 'rgba(255,255,255,0.01)' }}>
                    {versions.map((v, i) => (
                      <div
                        key={v.path}
                        className={`history-item ${selectedBrief?.path === v.path ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelect(v);
                        }}
                        style={{ paddingLeft: '40px', borderBottom: 'none' }}
                      >
                        <div className="history-meta" style={{ 
                          color: selectedBrief?.path === v.path ? 'var(--text-1)' : 'var(--text-3)',
                          fontWeight: selectedBrief?.path === v.path ? '600' : '400'
                        }}>
                          {v.filename?.replace('.md', '') || `Version ${versions.length - i}`}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="main-content" style={{ overflowY: 'auto', padding: '60px 40px' }}>
        {selectedBrief ? (
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ marginBottom: '32px', paddingBottom: '16px', borderBottom: '1px solid var(--border-soft)' }}>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--indigo)', marginBottom: '4px' }}>
                {selectedBrief.company}
              </div>
              <h1 style={{ fontSize: '24px', fontWeight: 800 }}>{selectedBrief.filename?.replace('.md', '')}</h1>
            </div>
            <MarkdownRenderer key={selectedBrief.path} content={selectedBrief.content || ''} />
          </div>
        ) : (
          <div className="brief-empty">
             <div className="brief-empty-icon">📂</div>
             <div className="brief-empty-text">Select a brief from the library</div>
          </div>
        )}
      </div>
    </div>
  );
}
