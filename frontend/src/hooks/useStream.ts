import { useCallback, useRef, useState } from "react";

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
  run: (companies: string[]) => void;
  reset: () => void;
}

const API_URL = "/api/v1/analyse";

export function useStream(): UseStreamReturn {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setEvents([]);
    setError(null);
    setIsLoading(false);
  }, []);

  const run = useCallback((companies: string[]) => {
    reset();
    setIsLoading(true);
    const controller = new AbortController();
    abortRef.current = controller;

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

          // Parse SSE frames
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
              setEvents((prev) => [...prev, evt]);

              if (eventLine === "end" || eventLine === "error") {
                setIsLoading(false);
              }
            } catch {
              // ignore parse errors on individual frames
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error).name !== "AbortError") {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg);
          setEvents((prev) => [...prev, { type: "error", error: msg }]);
        }
      } finally {
        setIsLoading(false);
      }
    })();
  }, [reset]);

  return { events, isLoading, error, run, reset };
}