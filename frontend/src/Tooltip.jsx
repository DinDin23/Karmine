/**
 * Small hover/focus-triggered tooltip. Works with mouse (hover) and keyboard
 * (the trigger is a real, tabbable button, shown via :focus-within), no JS
 * state needed.
 */
export default function Tooltip({ text }) {
  return (
    <span className="tooltip">
      <button type="button" className="tooltip-trigger" aria-label="More info">
        ?
      </button>
      <span className="tooltip-content" role="tooltip">
        {text}
      </span>
    </span>
  );
}
