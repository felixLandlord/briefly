import React, { useState } from 'react';
import { useStream } from './hooks/useStream';
import StreamWorkspace from './components/StreamWorkspace';
import HistoryView from './components/HistoryView';

type View = 'home' | 'history';
type Phase = 'idle' | 'running' | 'done';

export default function App() {
  const [view, setView] = useState<View>('home');
  const [phase, setPhase] = useState<Phase>('idle');
  const [inputVal, setInputVal] = useState('');
  const [companies, setCompanies] = useState<string[]>([]);
  
  const { events, isLoading, error, activeAgentNs, run, reset } = useStream();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = inputVal.split(',').map((c) => c.trim()).filter(Boolean);
    if (!parsed.length) return;
    setCompanies(parsed);
    setPhase('running');
    run(parsed);
  };

  const handleNewAnalysis = () => {
    reset();
    setPhase('idle');
    setView('home');
    setInputVal('');
  };

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <span style={{ color: 'var(--indigo)' }}>✦</span> Briefly
          </div>
        </div>
        
        <nav className="sidebar-nav">
          <button 
            className={`nav-link ${view === 'home' ? 'active' : ''}`}
            onClick={() => setView('home')}
          >
            <span>◈</span> New Analysis
          </button>
          <button 
            className={`nav-link ${view === 'history' ? 'active' : ''}`}
            onClick={() => setView('history')}
          >
            <span>📜</span> History
          </button>
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontSize: '11px', color: 'var(--text-4)' }}>
            Briefly v0.1.0
          </div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="main-content">
        {view === 'history' ? (
          <HistoryView />
        ) : (
          <>
            {phase === 'idle' && (
              <div className="home-page animate-fade-in">
                <div className="home-hero">
                  <p className="home-eyebrow">Multi-Agent Intelligence</p>
                  <h1 className="home-title">Competitive Intelligence</h1>
                  <p className="home-sub">
                    Get detailed briefs on any company. Our autonomous researchers and writers find the data you need in minutes.
                  </p>
                </div>

                <form className="home-form" onSubmit={handleSubmit}>
                  <input
                    className="home-input"
                    type="text"
                    value={inputVal}
                    onChange={(e) => setInputVal(e.target.value)}
                    placeholder="Enter companies (e.g. OpenAI, Anthropic)"
                    autoFocus
                  />
                  <button type="submit" className="btn btn-primary">
                    Analyze
                  </button>
                </form>
                
                <div style={{ marginTop: '24px', display: 'flex', gap: '20px' }}>
                   <div style={{ fontSize: '12px', color: 'var(--text-3)' }}>● Live Research</div>
                   <div style={{ fontSize: '12px', color: 'var(--text-3)' }}>● Competitive Briefs</div>
                   <div style={{ fontSize: '12px', color: 'var(--text-3)' }}>● Multi-Agent</div>
                </div>
              </div>
            )}

            {(phase === 'running' || phase === 'done') && (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <div style={{ 
                  height: '64px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between', 
                  padding: '0 24px',
                  borderBottom: '1px solid var(--border)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontWeight: 600 }}>{companies.join(' & ')}</span>
                    {!isLoading && <span style={{ color: 'var(--sage)', fontSize: '12px' }}>✓ Complete</span>}
                  </div>
                  <button className="btn btn-ghost" onClick={handleNewAnalysis}>
                    New Analysis
                  </button>
                </div>
                
                <StreamWorkspace 
                  events={events} 
                  isLoading={isLoading} 
                  activeAgentNs={activeAgentNs}
                  companies={companies}
                />
              </div>
            )}
          </>
        )}
        
        {error && (
          <div style={{ 
            position: 'absolute', 
            bottom: '24px', 
            right: '24px', 
            background: 'var(--rose)', 
            color: 'white', 
            padding: '12px 20px', 
            borderRadius: 'var(--r-md)',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 100
          }}>
            {error}
          </div>
        )}
      </main>
    </div>
  );
}
