import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchCustomers } from "../api.js";
import Logo from "./Logo.jsx";

// Dropdown login. Picking a customer is what "logs them in" — the backend then
// loads ONLY that customer's data (single-customer scoping).
export default function Login({ onLogin }) {
  const [customers, setCustomers] = useState([]);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchCustomers()
      .then((list) => {
        setCustomers(list);
        if (list.length) setSelected(list[0].id);
      })
      .catch(() => setError("Couldn't reach the server. Is the backend running?"));
  }, []);

  return (
    <motion.div
      className="login-card"
      initial={{ opacity: 0, y: 24, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <Logo size={52} />
      <h1 className="login-title">Welcome back 👋</h1>
      <p className="login-desc">Choose your account to start a secure support chat.</p>

      {error && <div className="error-banner">{error}</div>}

      <label className="field-label" htmlFor="cust">Account</label>
      <select
        id="cust"
        className="select"
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
      >
        {customers.map((c) => (
          <option key={c.id} value={c.id}>
            {c.firstName} · {c.id}
          </option>
        ))}
      </select>

      <motion.button
        className="primary-btn"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        disabled={!selected}
        onClick={() => {
          const c = customers.find((x) => x.id === selected);
          onLogin(c);
        }}
      >
        Continue to chat
      </motion.button>

      <p className="login-foot">🔒 Your private details are never shared in chat.</p>
    </motion.div>
  );
}
