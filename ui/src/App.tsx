import { Composer } from "./components/Composer";
import { MessageList } from "./components/MessageList";
import { useChat } from "./hooks/useChat";

export default function App() {
  const { messages, isSending, error, sendMessage } = useChat();

  return (
    <main className="app-shell">
      <section className="chat-card" aria-label="SWARMZ companion chat">
        <header className="chat-header">
          <h1>SWARMZ Companion</h1>
          <p>Connected to /v1/companion/message</p>
        </header>

        <MessageList messages={messages} isSending={isSending} />

        <Composer onSend={sendMessage} isSending={isSending} />

        {error ? <p className="chat-error">{error}</p> : null}
      </section>
    </main>
  );
}
