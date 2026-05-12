import { useMemo, useRef, useEffect, useState } from 'react';
import { StreamEvent, TokenEvent, UpdateEvent, EndEvent } from '../hooks/useStream';
import { getAgentInfo } from '../lib/agentUtils';
import MarkdownRenderer from './MarkdownRenderer';
import { Brief } from '../types';
import { fetchBrief } from '../lib/api';

interface StreamWorkspaceProps {
  events: StreamEvent[];
  isLoading: boolean;
  activeAgentNs: string[] | null;
  companies: string[];
}

type LogBlock = {
  id: string;
  agentInfo: ReturnType<typeof getAgentInfo>;
  content: string;
  toolCalls: Array<{ name: string; args: any }>;
  isUpdate: boolean;
  node?: string;
};

function buildLogBlocks(events: StreamEvent[]): LogBlock[] {
  const blocks: LogBlock[] = [];
  let currentBlock: LogBlock | null = null;

  for (const evt of events) {
    if ((evt.type === 'token' || evt.type === 'update') && 'ns' in evt) {
      const agentInfo = getAgentInfo((evt as any).source, (evt as any).ns, (evt as any).agent_name);
      const isToken = evt.type === 'token';
      const tokenContent = isToken ? (evt as TokenEvent).content : '';
      const toolCalls = !isToken && evt.type === 'update' ? (evt as UpdateEvent).tool_calls || [] : [];
      const node = !isToken && evt.type === 'update' ? (evt as UpdateEvent).node : undefined;
      const blockKey = `${(evt as any).agent_name || 'unknown'}-${(evt as any).source}`;

      if (currentBlock && currentBlock.id === blockKey && currentBlock.isUpdate === !isToken) {
        if (isToken) currentBlock.content += tokenContent;
        if (toolCalls.length) currentBlock.toolCalls.push(...toolCalls);
      } else {
        if (currentBlock) blocks.push(currentBlock);
        currentBlock = {
          id: blockKey,
          agentInfo,
          content: tokenContent,
          toolCalls,
          isUpdate: !isToken,
          node,
        };
      }
    } else if (evt.type === 'error') {
      if (currentBlock) { blocks.push(currentBlock); currentBlock = null; }
      blocks.push({ id: `error-${blocks.length}`, agentInfo: getAgentInfo('main', [], undefined), content: `Error: ${evt.error}`, toolCalls: [], isUpdate: false });
    }
  }
  if (currentBlock) blocks.push(currentBlock);
  return blocks;
}

export default function StreamWorkspace({ events, isLoading, activeAgentNs, companies }: StreamWorkspaceProps) {
  const logContainerRef = useRef<HTMLDivElement>(null);
  const briefContainerRef = useRef<HTMLDivElement>(null);
  const logBottomRef = useRef<HTMLDivElement>(null);
  const briefBottomRef = useRef<HTMLDivElement>(null);

  const [finalBriefs, setFinalBriefs] = useState<Brief[]>([]);
  const [selectedBriefIdx, setSelectedBriefIdx] = useState(0);
  const [isFetchingBriefs, setIsFetchingBriefs] = useState(false);
  const [hasAttemptedFetch, setHasAttemptedFetch] = useState(false);

  const logBlocks = useMemo(() => buildLogBlocks(events), [events]);

  // Check for EndEvent to trigger brief fetching
  useEffect(() => {
    const endEvent = events.find((e): e is EndEvent => e.type === 'end');
    if (endEvent && endEvent.briefs && endEvent.briefs.length > 0 && !hasAttemptedFetch && finalBriefs.length === 0) {
      console.log('[StreamWorkspace] End event detected, fetching briefs:', endEvent.briefs);
      setHasAttemptedFetch(true);
      loadFinalBriefs(endEvent.briefs);
    }
  }, [events, finalBriefs.length, hasAttemptedFetch]);

  const loadFinalBriefs = async (briefSpecs: any[]) => {
    try {
      setIsFetchingBriefs(true);
      console.log('[StreamWorkspace] Loading final briefs...', briefSpecs);
      const fullBriefs = await Promise.all(
        briefSpecs.map(async (spec) => {
          console.log(`[StreamWorkspace] Fetching brief for ${spec.company}...`);
          const content = await fetchBrief(spec.company, spec.filename);
          return { ...spec, content: content.content };
        })
      );
      console.log('[StreamWorkspace] Successfully loaded briefs:', fullBriefs.length);
      setFinalBriefs(fullBriefs);
    } catch (err) {
      console.error('[StreamWorkspace] Failed to fetch final briefs:', err);
    } finally {
      setIsFetchingBriefs(false);
    }
  };

  const activeAgent = useMemo(() => {
    if (!activeAgentNs || !Array.isArray(activeAgentNs) || !events.length) return null;
    const nsKey = activeAgentNs.join(',');
    // Iterate backwards to find the most recent event matching the current namespace
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e && (e.type === 'token' || e.type === 'update') && 'ns' in e) {
        if (Array.isArray(e.ns) && e.ns.join(',') === nsKey) {
          return getAgentInfo((e as any).source, (e as any).ns, (e as any).agent_name);
        }
      }
    }
    return null;
  }, [activeAgentNs, events]);

  // Smart scroll for Activity Log
  useEffect(() => {
    const container = logContainerRef.current;
    if (!container) return;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
    if (isNearBottom) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [events]);

  return (
    <div className="workspace">
      <div className="activity-panel">
        <div className="activity-header">
          <span className="activity-title">Activity Log</span>
          {isLoading && <div className="banner-dot" style={{ background: 'var(--indigo)' }} />}
        </div>
        <div className="activity-log" ref={logContainerRef}>
          {logBlocks.map((block, i) => (
            <div key={i} className="log-entry">
              <div className="agent-badge" style={{ color: block.agentInfo.textColor }}>
                <span className="agent-dot" style={{ background: block.agentInfo.dotColor }} />
                {block.agentInfo.label}
              </div>
              <div className="log-content">
                {block.content ? (
                  block.content
                ) : (
                  <div className="status-update">
                    {block.node === 'model_request' ? (
                      <span className="status-text italic opacity-70 text-xs">Thinking...</span>
                    ) : block.toolCalls.length > 0 ? (
                      <div className="tool-calls">
                        {block.toolCalls.map((tc, j) => (
                          <div key={j} className="tool-call">
                            <span className="tool-name text-xs font-mono text-[var(--indigo)]">{tc.name}</span>
                            {tc.args && (
                              <span className="tool-args text-[10px] opacity-60 ml-2">
                                {JSON.stringify(tc.args).substring(0, 100)}
                                {JSON.stringify(tc.args).length > 100 ? '...' : ''}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="status-text italic opacity-70 text-xs">Working...</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
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
        
        <div className="brief-container" ref={briefContainerRef}>
          {finalBriefs.length > 0 ? (
            <div className="final-brief-view">
              {finalBriefs.length > 1 && (
                <div className="brief-tabs">
                  {finalBriefs.map((b, idx) => (
                    <button 
                      key={idx} 
                      className={`brief-tab ${selectedBriefIdx === idx ? 'active' : ''}`}
                      onClick={() => setSelectedBriefIdx(idx)}
                    >
                      {b.company}
                    </button>
                  ))}
                </div>
              )}
              <div key={finalBriefs[selectedBriefIdx].path} className="animate-fade-in">
                <MarkdownRenderer content={finalBriefs[selectedBriefIdx].content || ''} />
              </div>
            </div>
          ) : isFetchingBriefs ? (
            <div className="brief-empty">
              <div className="banner-dot" style={{ background: 'var(--indigo)', width: '20px', height: '20px' }} />
              <div className="brief-empty-text">Finalizing briefs...</div>
            </div>
          ) : (
            <div className="brief-empty">
              <div className="brief-empty-icon">{isLoading ? '✦' : '⚠️'}</div>
              <div className="brief-empty-text">
                {isLoading 
                  ? `Agents are researching ${companies.join(', ')}...` 
                  : hasAttemptedFetch && finalBriefs.length === 0
                    ? "Analysis finished, but no briefs were found."
                    : "Analysis complete. Brief is ready."}
              </div>
            </div>
          )}
          <div ref={briefBottomRef} />
        </div>
      </div>
    </div>
  );
}
