export function LogoMark({ size = 30 }) {
  // WaterSphere mark: ward-network nodes joined by flow arcs inside a droplet
  // outline — one badge for header, landing, and login use.
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect x="1.5" y="1.5" width="29" height="29" rx="8" fill="#0b5fa5" stroke="#0b5fa5" />
      <path d="M16 5.5c3.4 4.1 6.5 7.6 6.5 11.4a6.5 6.5 0 1 1-13 0C9.5 13.1 12.6 9.6 16 5.5z"
        stroke="#ffffff" strokeWidth="1.8" strokeLinejoin="round" />
      <circle cx="13" cy="17.5" r="1.5" fill="#ffffff" />
      <circle cx="19" cy="17.5" r="1.5" fill="#ffffff" />
      <circle cx="16" cy="21" r="1.5" fill="#7fd1ff" />
      <path d="M13 17.5h6M16 17.5v3.5" stroke="#0b5fa5" strokeWidth="0.9" />
    </svg>
  );
}
