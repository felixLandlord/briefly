import { useMemo, useRef, useEffect, useState } from 'react';
import { useStream, TokenEvent, UpdateEvent, EndEvent } from './hooks/useStream';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// ── Helpers ──────────────────────────────────────────────────────────────────

function getAgentLabel(ns: string[]): string {
  const entry = ns.find((s) => s.startsWith('tools:'));
  if (!entry) return 'orchestrator';
  // "tools:website-researcher__abc123" → "website-researcher"
  return entry.replace('tools:', '').split('__')[0];
}

function getAgentClass(label: string): string {
  if (label === 'orchestrator') return 'agent-orchestrator';
  if (label.includes('researcher')) return 'agent-website-researcher';
  if (label.includes('writer')) return 'agent-brief-writer';
  return 'agent-default';
}

function isBriefWriter(ns: string[]): boolean {
  return ns.some((s) => s.includes('brief-writer'));
}

function fmtCompanies(companies: string[]): string {
  if (companies.length === 1) return companies[0];
  if (companies.length === 2) return companies.join(' & ');
  return companies.slice(0, -1).join(', ') + ' & ' + companies[companies.length - 1];
}

// ── Merged log items (consecutive same-agent tokens merged) ──────────────────

interface LogItem {
  id: string;
  agentLabel: string;
  content: string;
  type: 'token' | 'update';
}

function buildLog(events: (TokenEvent | UpdateEvent | EndEvent | { type: 'error'; error: string })[]): LogItem[] {
  const items: LogItem[] = [];
  for (const evt of events) {
    if (evt.type === 'token') {
      const te = evt as TokenEvent;
      const label = getAgentLabel(te.ns);
      const last = items[items.length - 1];
      if (last && last.agentLabel === label && last.type === 'token') {
        last.content += te.content;
      } else {
        items.push({ id: `${label}-${items.length}`, agentLabel: label, content: te.content, type: 'token' });
      }
    } else if (evt.type === 'update') {
      const ue = evt as UpdateEvent;
      const label = getAgentLabel(ue.ns);
      items.push({
        id: `update-${items.length}`,
        agentLabel: label,
        content: ue.node === 'model_request' ? `Thinking…` : `Using tools…`,
        type: 'update',
      });
    }
  }
  return items;
}

// ── Types ─────────────────────────────────────────────────────────────────────

type Phase = 'idle' | 'running' | 'done';

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const { events, isLoading, error, run, reset } = useStream();
  const [companies, setCompanies] = useState<string[]>([]);
  const [inputVal, setInputVal] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  const [activeTab, setActiveTab] = useState(0);

  const logBottomRef = useRef<HTMLDivElement>(null);
  const briefScrollRef = useRef<HTMLDivElement>(null);

  // Derived
  const logItems = useMemo(() => buildLog(events as any), [events]);

  const briefText = useMemo(() => {
    return events
      .filter((e): e is TokenEvent => e.type === 'token' && isBriefWriter((e as TokenEvent).ns))
      .map((e) => e.content)
      .join('');
  }, [events]);

  const endEvent = useMemo(
    () => events.find((e): e is EndEvent => e.type === 'end') as EndEvent | undefined,
    [events]
  );

  // Transition to done
  useEffect(() => {
    if (endEvent && phase === 'running') {
      setPhase('done');
    }
  }, [endEvent, phase]);

  // Auto-scroll log
  useEffect(() => {
    logBottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [logItems]);

  // Auto-scroll brief
  useEffect(() => {
    if (briefScrollRef.current) {
      briefScrollRef.current.scrollTop = briefScrollRef.current.scrollHeight;
    }
  }, [briefText]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = inputVal.split(',').map((c) => c.trim()).filter(Boolean);
    if (!parsed.length) return;
    setCompanies(parsed);
    setPhase('running');
    setActiveTab(0);
    run(parsed);
  };

  const handleReset = () => {
    reset();
    setCompanies([]);
    setInputVal('');
    setPhase('idle');
    setActiveTab(0);
  };

  // Multi-company tabs for done state
  const doneCompanies = endEvent?.companies ?? companies;

  return (
    <div className="app-shell">
      {/* ── Top Bar ── */}
      <header className="topbar">
        <span className="topbar-brand">Briefly</span>
        <div className="topbar-right">
          {phase !== 'idle' && (
            <button className="btn btn-ghost btn-sm" onClick={handleReset}>
              New Analysis
            </button>
          )}
        </div>
      </header>

      {/* ── Home ── */}
      {phase === 'idle' && (
        <div className="home-page animate-fade-in">
          <p className="home-eyebrow">Multi-Agent Intelligence</p>
          <h1 className="home-title">Briefly</h1>
          <p className="home-sub">
            Enter any company and our AI research team will produce a detailed competitive brief in minutes.
          </p>

          <form className="home-form" onSubmit={handleSubmit}>
            <div className="input-group">
              <input
                id="company-input"
                className="home-input"
                type="text"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                placeholder="OpenAI, Anthropic, Google DeepMind…"
                autoFocus
              />
              <button id="analyze-btn" type="submit" className="btn btn-primary">
                Generate Brief
              </button>
            </div>
            <p className="home-hint">Separate multiple companies with commas</p>
          </form>

          <div className="home-features">
            <div className="feature-item">
              <span className="feature-label">Researcher</span>
              <span className="feature-desc">Live web search</span>
            </div>
            <div className="feature-item">
              <span className="feature-label">Writer</span>
              <span className="feature-desc">Structured briefs</span>
            </div>
            <div className="feature-item">
              <span className="feature-label">Orchestrator</span>
              <span className="feature-desc">Multi-agent pipeline</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Running (streaming workspace) ── */}
      {phase === 'running' && (
        <div className="workspace animate-fade-in">
          {error && (
            <div className="error-bar">
              <span>⚠</span>
              <span>{error}</span>
            </div>
          )}
          <div className="workspace-header">
            <span className="workspace-companies">{fmtCompanies(companies)}</span>
            {isLoading ? (
              <span className="badge badge-running">
                <span className="dot-pulse" />
                Analyzing
              </span>
            ) : (
              <span className="badge badge-done">✓ Complete</span>
            )}
          </div>

          <div className="workspace-body">
            {/* Left: Activity Log */}
            <div className="activity-panel">
              <div className="panel-header">Agent Activity</div>
              <div className="activity-log">
                {logItems.map((item) =>
                  item.type === 'update' ? (
                    <div key={item.id} className="log-update-item">
                      <span className="log-update-text">
                        [{item.agentLabel}] {item.content}
                      </span>
                    </div>
                  ) : (
                    <div key={item.id} className="log-item">
                      <div className={`log-agent-label ${getAgentClass(item.agentLabel)}`}>
                        <span className="agent-dot" />
                        <span className="agent-name">{item.agentLabel}</span>
                      </div>
                      <div className="log-text">{item.content}</div>
                    </div>
                  )
                )}
                {logItems.length === 0 && (
                  <div style={{ padding: '24px 18px', color: 'var(--text-4)', fontSize: 12 }}>
                    Starting agents…
                  </div>
                )}
                <div ref={logBottomRef} />
              </div>
            </div>

            {/* Right: Brief Preview */}
            <div className="brief-panel">
              <div className="panel-header">Brief Preview</div>
              <div className="brief-scroll" ref={briefScrollRef}>
                {briefText ? (
                  <div className={`prose ${isLoading ? 'cursor-blink' : ''}`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{briefText}</ReactMarkdown>
                  </div>
                ) : (
                  <div className="brief-empty">
                    <div className="brief-empty-icon">✦</div>
                    <div className="brief-empty-text">Brief will appear here as it's written</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Done ── */}
      {phase === 'done' && (
        <div className="done-page animate-fade-in">
          <div className="done-header">
            {doneCompanies.length > 1 ? (
              <div className="done-tabs">
                {doneCompanies.map((c, i) => (
                  <button
                    key={c}
                    className={`done-tab ${activeTab === i ? 'active' : ''}`}
                    onClick={() => setActiveTab(i)}
                    id={`tab-${c.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            ) : (
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-1)' }}>
                {doneCompanies[0]}
              </span>
            )}
            <span className="badge badge-done">✓ Analysis complete</span>
          </div>

          <div className="done-content">
            <div className="prose">
              {briefText ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{briefText}</ReactMarkdown>
              ) : (
                <p style={{ color: 'var(--text-3)' }}>No brief content captured.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
