import { useEffect, useRef, useState } from "react";

const BACKEND_URL = "http://127.0.0.1:8000";
const RECENT_MESSAGES_TO_KEEP = 4;

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "안녕하세요. 질문을 입력하면 실시간 Streaming 방식으로 답변합니다. 대화가 길어지면 오래된 내용은 자동으로 요약해서 기억합니다.",
    },
  ]);

  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [summary, setSummary] = useState("");

  const [tokenInfo, setTokenInfo] = useState({
    model: "-",
    summaryUsed: false,
    summaryTriggerTokens: 500,
    recentMessagesToKeep: RECENT_MESSAGES_TO_KEEP,
    maxOutputTokens: "-",
    estimatedBeforeSummaryTokens: "-",
    estimatedInputTokens: "-",
    estimatedOutputTokens: "-",
    estimatedTotalTokens: "-",
    note: "누적 토큰이 기준치를 넘으면 오래된 대화를 요약하고, 최근 대화만 유지합니다.",
  });

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const userMessage = input.trim();
    if (!userMessage || isStreaming) return;

    setInput("");

    const newUserMessage = {
      role: "user",
      content: userMessage,
    };

    const emptyAssistantMessage = {
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, newUserMessage, emptyAssistantMessage]);
    setIsStreaming(true);

    try {
      const historyForRequest = messages.filter(
        (msg) => msg.content.trim() !== ""
      );

      const response = await fetch(`${BACKEND_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage,
          history: historyForRequest,
          summary: summary,
        }),
      });

      if (!response.ok) {
        throw new Error(`서버 오류가 발생했습니다. status=${response.status}`);
      }

      if (!response.body) {
        throw new Error("Streaming 응답을 받을 수 없습니다.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";
      let updatedSummary = summary;

      while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const eventText of events) {
          const parsedEvent = parseSSEEvent(eventText);
          if (!parsedEvent) continue;

          if (parsedEvent.event === "meta") {
            updatedSummary = parsedEvent.data.summary || "";
            setSummary(updatedSummary);

            setTokenInfo((prev) => ({
              ...prev,
              model: parsedEvent.data.model,
              summaryUsed: parsedEvent.data.summaryUsed,
              summaryTriggerTokens: parsedEvent.data.summaryTriggerTokens,
              recentMessagesToKeep: parsedEvent.data.recentMessagesToKeep,
              maxOutputTokens: parsedEvent.data.maxOutputTokens,
              estimatedBeforeSummaryTokens:
                parsedEvent.data.estimatedBeforeSummaryTokens,
              estimatedInputTokens: parsedEvent.data.estimatedInputTokens,
              note: parsedEvent.data.note,
            }));

            // 요약이 발생하면 화면에서도 오래된 원문 메시지를 줄인다.
            if (parsedEvent.data.summaryUsed) {
              setMessages((prevMessages) => {
                return prevMessages.slice(-RECENT_MESSAGES_TO_KEEP - 2);
              });
            }
          }

          if (parsedEvent.event === "message") {
            const delta = parsedEvent.data.delta;

            setMessages((prevMessages) => {
              const updatedMessages = [...prevMessages];
              const lastIndex = updatedMessages.length - 1;

              updatedMessages[lastIndex] = {
                ...updatedMessages[lastIndex],
                content: updatedMessages[lastIndex].content + delta,
              };

              return updatedMessages;
            });
          }

          if (parsedEvent.event === "done") {
            setSummary(parsedEvent.data.summary || updatedSummary);

            setTokenInfo((prev) => ({
              ...prev,
              summaryUsed: parsedEvent.data.summaryUsed,
              estimatedOutputTokens: parsedEvent.data.estimatedOutputTokens,
              estimatedTotalTokens: parsedEvent.data.estimatedTotalTokens,
            }));
          }

          if (parsedEvent.event === "error") {
            throw new Error(parsedEvent.data.message);
          }
        }
      }
    } catch (error) {
      console.error(error);

      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        const lastIndex = updatedMessages.length - 1;

        updatedMessages[lastIndex] = {
          ...updatedMessages[lastIndex],
          content: `오류가 발생했습니다: ${error.message}`,
        };

        return updatedMessages;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleClearChat = () => {
    if (isStreaming) return;

    setMessages([
      {
        role: "assistant",
        content:
          "대화가 초기화되었습니다. 새 질문을 입력하면 다시 Streaming 응답을 시작합니다.",
      },
    ]);

    setSummary("");

    setTokenInfo({
      model: "-",
      summaryUsed: false,
      summaryTriggerTokens: 500,
      recentMessagesToKeep: RECENT_MESSAGES_TO_KEEP,
      maxOutputTokens: "-",
      estimatedBeforeSummaryTokens: "-",
      estimatedInputTokens: "-",
      estimatedOutputTokens: "-",
      estimatedTotalTokens: "-",
      note: "누적 토큰이 기준치를 넘으면 오래된 대화를 요약하고, 최근 대화만 유지합니다.",
    });
  };

  return (
    <div className="min-h-screen bg-slate-200 p-4 text-slate-900">
      <div className="mx-auto max-w-7xl">
        {/* 상단 제목 박스 */}
        <section className="mb-4 rounded-3xl bg-white p-6 shadow-lg">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-bold text-blue-600">
                LLM API Streaming Chat Project
              </p>
              <h1 className="mt-2 text-3xl font-black text-slate-900">
                1:1 AI 채팅 환경 구축
              </h1>
              <p className="mt-2 text-sm text-slate-500">
                React + Vite + Tailwind CSS + FastAPI + OpenAI SDK + SSE
              </p>
            </div>

            <button
              onClick={handleClearChat}
              disabled={isStreaming}
              className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-bold text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              대화 초기화
            </button>
          </div>
        </section>

        <div className="grid gap-4 xl:grid-cols-[1fr_380px]">
          {/* 왼쪽 채팅 박스 */}
          <section className="overflow-hidden rounded-3xl bg-white shadow-lg">
            <div className="border-b border-slate-200 bg-slate-900 px-6 py-4 text-white">
              <h2 className="text-lg font-bold">채팅 화면</h2>
              <p className="mt-1 text-sm text-slate-300">
                사용자 메시지와 AI Streaming 응답이 실시간으로 표시됩니다.
              </p>
            </div>

            <div className="h-[590px] overflow-y-auto bg-slate-50 p-5">
              <div className="mx-auto flex max-w-4xl flex-col gap-5">
                {summary && (
                  <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 shadow-sm">
                    <div className="mb-2 text-sm font-bold text-blue-700">
                      요약 메모리 적용 중
                    </div>
                    <p className="text-sm leading-7 text-blue-900">
                      {summary}
                    </p>
                  </div>
                )}

                {messages.map((message, index) => (
                  <ChatMessage key={index} message={message} />
                ))}

                {isStreaming && (
                  <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
                    <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-blue-600"></span>
                    AI가 답변을 생성하는 중입니다...
                  </div>
                )}

                <div ref={bottomRef} />
              </div>
            </div>

            {/* 입력창 박스 */}
            <div className="border-t border-slate-200 bg-white p-5">
              <form onSubmit={handleSubmit} className="flex flex-col gap-3 md:flex-row">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={isStreaming}
                  placeholder="질문을 입력하세요..."
                  className="flex-1 rounded-2xl border border-slate-300 bg-slate-50 px-5 py-4 text-sm outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
                />

                <button
                  type="submit"
                  disabled={isStreaming || !input.trim()}
                  className="rounded-2xl bg-blue-600 px-8 py-4 text-sm font-black text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {isStreaming ? "응답 중..." : "전송"}
                </button>
              </form>

              <p className="mt-3 text-xs text-slate-400">
                OpenAI API Key는 frontend에 저장하지 않고 backend의 .env 파일에서만 관리합니다.
              </p>
            </div>
          </section>

          {/* 오른쪽 정보 박스들 */}
          <aside className="flex flex-col gap-4">
            <section className="rounded-3xl bg-white p-5 shadow-lg">
              <h2 className="text-lg font-black text-slate-900">
                토큰 관리 전략
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                누적 예상 토큰이 500 이상이 되면 오래된 대화를 요약하고,
                원문 대화는 줄인 뒤 요약본과 최근 대화만 사용합니다.
              </p>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <InfoBox
                  label="요약 기준"
                  value={tokenInfo.summaryTriggerTokens}
                  unit="tokens"
                />
                <InfoBox
                  label="최근 유지"
                  value={tokenInfo.recentMessagesToKeep}
                  unit="messages"
                />
                <InfoBox
                  label="최대 출력"
                  value={tokenInfo.maxOutputTokens}
                  unit="tokens"
                />
                <InfoBox
                  label="요약 사용"
                  value={tokenInfo.summaryUsed ? "ON" : "OFF"}
                  unit={tokenInfo.summaryUsed ? "summary" : "waiting"}
                />
              </div>
            </section>

            <section className="rounded-3xl bg-white p-5 shadow-lg">
              <h2 className="text-lg font-black text-slate-900">
                토큰 추정치
              </h2>

              <div className="mt-4 flex flex-col gap-3">
                <TokenRow label="모델" value={tokenInfo.model} />
                <TokenRow
                  label="요약 전 예상 토큰"
                  value={tokenInfo.estimatedBeforeSummaryTokens}
                />
                <TokenRow
                  label="현재 입력 토큰"
                  value={tokenInfo.estimatedInputTokens}
                />
                <TokenRow
                  label="예상 출력 토큰"
                  value={tokenInfo.estimatedOutputTokens}
                />
                <TokenRow
                  label="예상 총 토큰"
                  value={tokenInfo.estimatedTotalTokens}
                />
              </div>
            </section>

            <section className="rounded-3xl bg-white p-5 shadow-lg">
              <h2 className="text-lg font-black text-slate-900">
                요약 메모리
              </h2>

              {summary ? (
                <div className="mt-4 max-h-60 overflow-y-auto rounded-2xl border border-blue-200 bg-blue-50 p-4 text-sm leading-7 text-blue-900">
                  {summary}
                </div>
              ) : (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 text-slate-500">
                  아직 요약된 대화가 없습니다. 대화가 길어져 기준 토큰을 넘으면
                  이 영역에 요약 메모리가 표시됩니다.
                </div>
              )}
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}

function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] ${isUser ? "text-right" : "text-left"}`}>
        <div
          className={`mb-1 text-xs font-bold ${
            isUser ? "text-blue-600" : "text-slate-500"
          }`}
        >
          {isUser ? "사용자" : "AI"}
        </div>

        <div
          className={`whitespace-pre-wrap rounded-3xl px-5 py-4 text-sm leading-7 shadow-sm ${
            isUser
              ? "rounded-tr-md bg-blue-600 text-white"
              : "rounded-tl-md border border-slate-200 bg-white text-slate-800"
          }`}
        >
          {message.content || " "}
        </div>
      </div>
    </div>
  );
}

function InfoBox({ label, value, unit }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-bold text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{unit}</p>
    </div>
  );
}

function TokenRow({ label, value }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-black text-slate-900">{value}</span>
    </div>
  );
}

function parseSSEEvent(eventText) {
  const lines = eventText.split("\n");

  let eventName = "";
  let dataText = "";

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.replace("event:", "").trim();
    }

    if (line.startsWith("data:")) {
      dataText = line.replace("data:", "").trim();
    }
  }

  if (!eventName || !dataText) {
    return null;
  }

  try {
    return {
      event: eventName,
      data: JSON.parse(dataText),
    };
  } catch {
    return null;
  }
}

export default App;