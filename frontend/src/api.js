// Tiny API client for the FastAPI backend.
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchCustomers() {
  const res = await fetch(`${BASE}/customers`);
  if (!res.ok) throw new Error("Could not load customers");
  return res.json();
}

export async function sendChat(customerId, message) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_id: customerId, message }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || "Something went wrong");
  }
  return res.json();
}
