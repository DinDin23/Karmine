// Original crown mark — three peaks over a base band, not traced from any
// Supercell/Clash Royale asset. Used as the Karmine wordmark icon and as
// the source for public/favicon.svg.
export default function Logo({ className, size = 28 }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <rect x="3" y="17" width="18" height="3" rx="1" />
      <path d="M4 15.5 2.5 7l5 3.2L12 4l4.5 6.2 5-3.2-1.5 8.5H4Z" />
      <circle cx="4" cy="6" r="1.4" />
      <circle cx="12" cy="3" r="1.4" />
      <circle cx="20" cy="6" r="1.4" />
    </svg>
  );
}
