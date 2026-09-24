/**
 * Collapsible "Where do I find this?" help under a form field. Uses native
 * <details>, so it's keyboard-accessible with no JS state. The screenshot is
 * optional so the steps can ship before images exist.
 */
export default function HelpSteps({ steps, image, imageAlt }) {
  return (
    <details className="help-steps">
      <summary>Where do I find this?</summary>
      <ol>
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      {image && <img src={image} alt={imageAlt} loading="lazy" />}
    </details>
  );
}
