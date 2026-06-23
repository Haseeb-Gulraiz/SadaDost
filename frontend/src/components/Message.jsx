import { motion } from "framer-motion";

// One chat bubble. Bot messages show small meta chips (decision / confidence / safety)
// so the grounding and guardrails are visible during the demo.
const ACTION_LABEL = {
  answer: "Answered",
  escalate: "Escalated to human",
  decline: "Out of scope",
  refuse: "Refused",
};

export default function Message({ msg }) {
  const isUser = msg.role === "user";
  const showChips = !isUser && (msg.action || msg.pii_redacted);
  return (
    <motion.div
      className={`bubble-row ${isUser ? "from-user" : "from-bot"}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className={`bubble ${isUser ? "user" : "bot"}`}>
        <p className="bubble-text">{msg.text}</p>
        {showChips && (
          <div className="chips">
            {msg.action && (
              <span className={`chip ${msg.action === "answer" ? "" : "warn"}`}>
                {ACTION_LABEL[msg.action] || msg.action}
              </span>
            )}
            {msg.pii_redacted && <span className="chip danger">PII redacted</span>}
          </div>
        )}
      </div>
    </motion.div>
  );
}
