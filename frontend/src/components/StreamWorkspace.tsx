import { useMemo, useRef, useEffect } from 'react';
import { StreamEvent, TokenEvent, UpdateEvent } from '../hooks/useStream';
import { getAgentInfo } from '../lib/agentUtils';
import MarkdownRenderer from './MarkdownRenderer';

interface StreamWorkspaceProps {
  events: StreamEvent[];
  isLoading: boolean;
  activeAgentNs: string[] | null;
  companies: string[];
}

export default function StreamWorkspace({ events, isLoading, activeAgentNs, companies }: StreamWorkspaceProps) {
  const logBottomRef = useRef<HTMLDivElement>(null);
  const briefBottomRef = useRef<HTMLDivElement>(null);

  const briefText = useMemo(() => {
    return events
      .filter((e): e is TokenEvent => e.type === 'token' && getAgentInfo(e.source, e.ns).isWriter)
      .map((e) => e.content)
      .join('');
  }, [events]);

  const activeAgent = useMemo(() => {
    if (!activeAgentNs) return null;
    // We need source here too, let's find the last event with this ns
    const lastEvent = [...events].reverse().find(e => (e.type === 'token' || e.type === 'update') && JSON.stringify(e.ns) === JSON.stringify(activeAgentNs));
    if (lastEvent && (lastEvent.type === 'token' || lastEvent.type === 'update')) {
      return getAgentInfo(lastEvent.source, lastEvent.ns);
    }
    return null;
  }, [activeAgentNs, events]);

  useEffect(() => {
    logBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  useEffect(() => {
    briefBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [briefText]);

  return (
    <div className="workspace">
      <div className="activity-panel">
        <div className="activity-header">
          <span className="activity-title">Activity Log</span>
          {isLoading && <div className="banner-dot" style={{ background: 'var(--indigo)' }} />}
        </div>
        <div className="activity-log">
          {events.map((evt, i) => {
            if (evt.type === 'token' || evt.type === 'update') {
              const info = getAgentInfo(evt.source, evt.ns);
              return (
                <div key={i} className="log-entry">
                  <div className="agent-badge" style={{ color: info.textColor }}>
                    <span className="agent-dot" style={{ background: info.dotColor }} />
                    {info.label}
                  </div>
                  <div className="log-content">
                    {evt.type === 'token' ? evt.content : `[${evt.node === 'model_request' ? 'Thinking' : 'Using tools'}]`}
                  </div>
                </div>
              );
            }
            if (evt.type === 'error') {
              return (
                <div key={i} className="log-entry" style={{ color: 'var(--rose)' }}>
                  <strong>Error:</strong> {evt.error}
                </div>
              );
            }
            return null;
          })}
          <div ref={logBottomRef} />
        </div>
      </div>

      <div className="stream-panel">
        {activeAgent && isLoading && (
          <div className="active-agent-banner">
            <div className="banner-dot" style={{ background: activeAgent.dotColor }} />
            <span className="banner-text">{activeAgent.label} is working...</span>
          </div>
        )}
        
        <div className="brief-container">
          <div className="prose">
            {briefText ? (
              isLoading ? (
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font)', fontSize: '15px', color: 'var(--text-1)' }}>
                  {briefText}
                  <span className="cursor-blink" />
                </pre>
              ) : (
                <MarkdownRenderer content={briefText} />
              )
            ) : (
              <div className="brief-empty">
                <div className="brief-empty-icon">✦</div>
                <div className="brief-empty-text">Agents are researching {companies.join(', ')}...</div>
              </div>
            )}
            <div ref={briefBottomRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
