/**
 * StepIndicator: progress dots for multi-step forms.
 * @param {number} currentStep - 1-based current step
 * @param {number} totalSteps
 */
const StepIndicator = ({ currentStep, totalSteps }) => (
  <div className="flex items-center justify-center gap-2" role="img" aria-label={`Step ${currentStep} of ${totalSteps}`}>
    {Array.from({ length: totalSteps }, (_, i) => {
      const step = i + 1;
      const active = step === currentStep;
      const done = step < currentStep;
      return (
        <span
          key={step}
          className={`h-2.5 rounded-full motion-safe:transition-all motion-safe:duration-300 ${
            active ? 'w-8 bg-primary-strong' : done ? 'w-2.5 bg-primary' : 'w-2.5 bg-border'
          }`}
          aria-hidden="true"
        />
      );
    })}
  </div>
);

export default StepIndicator;
