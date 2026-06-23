import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { sendChat } from "../api.js";
import Logo from "./Logo.jsx";
import Message from "./Message.jsx";

export default function Chat({ customer, onLogout }) {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: `Hi ${customer.firstName}! I'm SadaDost. Ask me about your card, balance, refunds, OTPs and more.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setSending(true);
    try {
      const res = await sendChat(customer.id, text);
      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: res.reply,
          action: res.action,
          pii_redacted: res.pii_redacted,
        },
      ]);
    } catch (err) {
      setMessages((m) => [...m, { role: "bot", text: `⚠️ ${err.message}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <motion.div
      className="chat-card"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <header className="chat-header">
        <Logo size={34} />
        <div className="chat-user">
          <span className="who">{customer.firstName}</span>
          <button className="link-btn" onClick={onLogout}>Switch</button>
        </div>
      </header>

      <div className="messages">
        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <Message key={i} msg={m} />
          ))}
        </AnimatePresence>

        {sending && (
          <motion.div className="bubble-row from-bot" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="bubble bot typing">
              <span></span><span></span><span></span>
            </div>
          </motion.div>
        )}
        <div ref={endRef} />
      </div>

      <div className="composer">
        <input
          className="composer-input"
          placeholder="Type your message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <motion.button
          className="send-btn"
          whileTap={{ scale: 0.9 }}
          onClick={handleSend}
          disabled={sending || !input.trim()}
        >
          Send
        </motion.button>
      </div>
    </motion.div>
  );
}
