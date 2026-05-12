import { useCallback, useRef, useState, useEffect } from "react";

export type TokenEvent = {
  type: "token";
  source: "main" | "subagent";
  content: string;
  ns: string[];
};

export type UpdateEvent = {
  type: "update";
  source: "main" | "subagent";
  node: string;
  ns: string[];
};

export type EndEvent = {
  type: "end";
  thread_id: string;
  companies: string[];
  briefs: Array<{ company: string; path: string; filename: string }>;
};

export type ErrorEvent = { type: "error"; error: string };

export type StreamEvent = TokenEvent | UpdateEvent | EndEvent | ErrorEvent;

export interface UseStreamReturn {
  events: StreamEvent[];
  isLoading: boolean;
  error: string | null;
  activeAgentNs: string[] | null;
  run: (companies: string[]) => void;
  reset: () => void;
}

const API_URL = "/api/v1/analyse";

export function useStream(): UseStreamReturn {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeAgentNs, setActiveAgentNs] = useState<string[] | null>(null);
  
  const abortRef = useRef<AbortController | null>(null);
  const eventBufferRef = useRef<StreamEvent[]>([]);
  const rafRef = useRef<number | null>(null);

  const flushBuffer = useCallback(() => {
    if (eventBufferRef.current.length > 0) {
      const newEvents = [...eventBufferRef.current];
      eventBufferRef.current = [];
      
      setEvents((prev) => [...prev, ...newEvents]);
      
      // Update active agent based on the last event with ns
      for (let i = newEvents.length - 1; i >= 0; i--) {
        const evt = newEvents[i];
        if (evt.type === "token" || evt.type === "update") {
          setActiveAgentNs(evt.ns);
          break;
        }
      }
    }
    rafRef.current = requestAnimationFrame(flushBuffer);
  }, []);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setEvents([]);
    setError(null);
    setIsLoading(false);
    setActiveAgentNs(null);
    eventBufferRef.current = [];
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const run = useCallback((companies: string[]) => {
    reset();
    setIsLoading(true);
    const controller = new AbortController();
    abortRef.current = controller;
    
    // Start RAF loop
    rafRef.current = requestAnimationFrame(flushBuffer);

    (async () => {
      try {
        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ companies }),
          signal: controller.signal,
        });

        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const frames = buffer.split("\n\n");
          buffer = frames.pop() ?? "";

          for (const frame of frames) {
            if (!frame.trim()) continue;
            const eventLine = frame.match(/^event: (.+)$/m)?.[1];
            const dataLine = frame.match(/^data: (.+)$/m)?.[1];
            if (!eventLine || !dataLine) continue;

            try {
              const parsed = JSON.parse(dataLine.replace(/\\n/g, "\n"));
              const evt: StreamEvent = { type: eventLine as StreamEvent["type"], ...parsed };
              
              eventBufferRef.current.push(evt);

              if (eventLine === "end" || eventLine === "error") {
                // Final flush will happen in the loop or after
              }
            } catch {
              // ignore parse errors
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error).name !== "AbortError") {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg);
          eventBufferRef.current.push({ type: "error", error: msg });
        }
      } finally {
        // Wait a bit to ensure last events are flushed then stop loading
        setTimeout(() => {
          setIsLoading(false);
          if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
          }
        }, 100);
      }
    })();
  }, [reset, flushBuffer]);

  return { events, isLoading, error, activeAgentNs, run, reset };
}