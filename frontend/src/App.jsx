import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import Login from "./components/Login.jsx";
import Chat from "./components/Chat.jsx";

export default function App() {
  const [customer, setCustomer] = useState(null);

  return (
    <div className="app-bg">
      <div className="app-shell">
        <AnimatePresence mode="wait">
          {!customer ? (
            <Login key="login" onLogin={setCustomer} />
          ) : (
            <Chat key="chat" customer={customer} onLogout={() => setCustomer(null)} />
          )}
        </AnimatePresence>
      </div>
      <footer className="app-footer">SadaDost · grounded & safe support</footer>
    </div>
  );
}
