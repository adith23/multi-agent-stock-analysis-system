export interface ServerSentEvent {
  id: string;
  event: string;
  data: string;
  retry?: number;
}

export interface FetchEventSourceInit extends Omit<RequestInit, "headers"> {
  headers?: Record<string, string>;
  onopen?: (response: Response) => Promise<void> | void;
  onmessage?: (event: ServerSentEvent) => void;
  onclose?: () => void;
  onerror?: (err: unknown) => number | null | undefined | void;
  onHeartbeat?: () => void;
  openWhenHidden?: boolean;
}

const DEFAULT_RETRY_INTERVAL_MS = 1000;
const MAX_RETRY_INTERVAL_MS = 30000;

export async function fetchEventSource(
  input: RequestInfo | URL,
  {
    signal,
    headers: inputHeaders,
    onopen,
    onmessage,
    onclose,
    onerror,
    onHeartbeat,
    ...rest
  }: FetchEventSourceInit,
): Promise<void> {
  let retryInterval = DEFAULT_RETRY_INTERVAL_MS;
  let lastEventId = "";

  while (!signal?.aborted) {
    let curEvent = "";
    let curData = "";
    let curId = "";
    let curRetry: number | undefined;

    const headers: Record<string, string> = {
      Accept: "text/event-stream",
      ...(inputHeaders ?? {}),
    };

    if (lastEventId) {
      headers["Last-Event-ID"] = lastEventId;
    }

    try {
      const response = await fetch(input, {
        ...rest,
        headers,
        signal,
      });

      if (signal?.aborted) return;

      if (!response.ok) {
        throw new Error(
          `SSE HTTP error: ${response.status} ${response.statusText}`,
        );
      }

      const contentType = response.headers.get("content-type") ?? "";
      if (!contentType.includes("text/event-stream")) {
        throw new Error(
          `Expected text/event-stream but received ${contentType}`,
        );
      }

      if (onopen) {
        await onopen(response);
      }

      // Reset retry backoff on successful connection
      retryInterval = DEFAULT_RETRY_INTERVAL_MS;

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Response body is not readable.");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (!signal?.aborted) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split(/\r\n|\r|\n/);
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith(":")) {
            // Heartbeat comment
            onHeartbeat?.();
            continue;
          }

          if (line === "") {
            // Dispatch event on empty line
            if (curData) {
              const event: ServerSentEvent = {
                id: curId || lastEventId,
                event: curEvent || "message",
                data: curData.endsWith("\n") ? curData.slice(0, -1) : curData,
                retry: curRetry,
              };
              if (curId) {
                lastEventId = curId;
              }
              onmessage?.(event);
            }
            curEvent = "";
            curData = "";
            curId = "";
            curRetry = undefined;
            continue;
          }

          const colonIdx = line.indexOf(":");
          let field: string;
          let val: string;

          if (colonIdx === -1) {
            field = line;
            val = "";
          } else {
            field = line.slice(0, colonIdx);
            val = line.slice(colonIdx + 1);
            if (val.startsWith(" ")) {
              val = val.slice(1);
            }
          }

          if (field === "event") {
            curEvent = val;
          } else if (field === "data") {
            curData += `${val}\n`;
          } else if (field === "id") {
            curId = val;
          } else if (field === "retry") {
            const parsed = parseInt(val, 10);
            if (!Number.isNaN(parsed)) {
              curRetry = parsed;
              retryInterval = parsed;
            }
          }
        }
      }

      if (signal?.aborted) {
        return;
      }

      onclose?.();
      return;
    } catch (err) {
      if (signal?.aborted) {
        return;
      }

      const customRetry = onerror ? onerror(err) : undefined;
      if (typeof customRetry === "number") {
        retryInterval = customRetry;
      }

      // Exponential backoff
      await new Promise((resolve) => setTimeout(resolve, retryInterval));
      retryInterval = Math.min(retryInterval * 1.5, MAX_RETRY_INTERVAL_MS);
    }
  }
}
