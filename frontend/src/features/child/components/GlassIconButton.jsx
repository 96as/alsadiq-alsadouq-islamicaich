/**
 * GlassIconButton — reusable frosted-glass circular icon button.
 *
 * @param {React.ElementType} icon     - Lucide icon component (e.g. Volume2)
 * @param {Function}          onClick  - click handler
 * @param {string}            ariaLabel - accessible label (required)
 * @param {string}            className - optional extra classes
 * @param {boolean}           pressed   - hotfix-2: a toggle's state (aria-pressed); omit for a plain button
 * @param {string}            title     - hotfix-2: tooltip
 */
const GlassIconButton = (props) => {
  const LucideIcon = props.icon;

  return (
    <button
      onClick={props.onClick}
      className={`glass-button group relative h-11 w-11 rounded-full grid place-items-center shrink-0 transition-shadow ${props.className || ''}`}
      aria-label={props.ariaLabel}
      aria-pressed={props.pressed} // hotfix-2
      title={props.title} // hotfix-2
      data-toggle={props.dataToggle} // hotfix-2
    >
      <LucideIcon className="relative h-5 w-5 text-white/90" strokeWidth={1.5} />
    </button>
  );
};

export default GlassIconButton;
