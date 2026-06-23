// SadaDost wordmark + mark. "Sada Dost" = an honest, simple friend.
export default function Logo({ size = 36 }) {
  return (
    <div className="logo">
      <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden>
        <rect x="3" y="3" width="42" height="42" rx="13" fill="url(#sd-grad)" />
        {/* friendly speech bubble */}
        <path
          d="M14 17.5A3.5 3.5 0 0 1 17.5 14h13a3.5 3.5 0 0 1 3.5 3.5v8a3.5 3.5 0 0 1-3.5 3.5H22l-5 4v-4h-.5A3.5 3.5 0 0 1 13 25.5z"
          transform="translate(1 0)"
          fill="white"
          opacity="0.95"
        />
        {/* heart dot = trust */}
        <circle cx="24" cy="21.5" r="2.1" fill="#0E7C66" />
        <defs>
          <linearGradient id="sd-grad" x1="3" y1="3" x2="45" y2="45">
            <stop stopColor="#10B981" />
            <stop offset="1" stopColor="#0E7C66" />
          </linearGradient>
        </defs>
      </svg>
      <div className="logo-text">
        <span className="logo-name">SadaDost</span>
        <span className="logo-sub">PayWallet Support</span>
      </div>
    </div>
  );
}
