export default function Logo({ size = 36, id = 'logo' }) {
  const gradId = `logoGrad-${id}`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="CodeSwitch logo"
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#7c6af7" />
          <stop offset="100%" stopColor="#a78bfa" />
        </linearGradient>
      </defs>

      {/* Background */}
      <rect width="40" height="40" rx="10" fill={`url(#${gradId})`} />

      {/* Left angle bracket < */}
      <path
        d="M15 10L7 20L15 30"
        stroke="white"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Right angle bracket > */}
      <path
        d="M25 10L33 20L25 30"
        stroke="white"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Exchange arrow — top (left to right) */}
      <path
        d="M17.5 17H22.5"
        stroke="rgba(255,255,255,0.88)"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M20.5 14.8L22.8 17L20.5 19.2"
        stroke="rgba(255,255,255,0.88)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Exchange arrow — bottom (right to left) */}
      <path
        d="M22.5 23H17.5"
        stroke="rgba(255,255,255,0.88)"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M19.5 20.8L17.2 23L19.5 25.2"
        stroke="rgba(255,255,255,0.88)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
