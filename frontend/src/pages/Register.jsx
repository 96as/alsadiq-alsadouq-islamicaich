import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserPlus, ArrowRight, ArrowLeft, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthLayout from '../features/auth/components/AuthLayout';
import AuthField from '../features/auth/components/AuthField';
import AuthHeader from '../features/auth/components/AuthHeader';
import ButtonLink from '../features/auth/components/ButtonLink';
import useDialogFocus from '../features/auth/useDialogFocus';
import PasswordToggle from '../features/auth/components/PasswordToggle';
import { Button, Card, IconButton } from '../components/ui';
import StepIndicator from '../features/auth/components/StepIndicator';
import { ROUTES } from '../routes';
import { validateStrongPassword } from '../utils/validators';
import { assetUrl } from '../utils/assetUrl'; // cards-spec (05)
import { REGISTRATION_STRINGS } from '../features/child/ai/aiStrings'; // cards-spec (05)

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// cards-spec (05) review: "11. AI Companion. Al-Sadiq is..." -> ["11. AI Companion.", "Al-Sadiq is..."] (number and title, then the body).
function clauseParts(text) {
  const end = text.indexOf('. ', text.indexOf('. ') + 2);
  return end < 0 ? [text, ''] : [text.slice(0, end + 1), text.slice(end + 2)];
}
const TOTAL_STEPS = 3;

const STEP_TITLES = [
  { title: 'Create Account', subtitle: 'Tell us your name' },
  { title: 'Contact Info', subtitle: 'How we can reach you' },
  { title: 'Set Password', subtitle: 'Secure your account' },
];

function validateStep(step, values) {
  const next = {};
  const trim = (key) => (values[key] ?? '').trim();

  if (step === 1) {
    if (!trim('first_name')) next.first_name = 'Please enter your first name.';
    if (!trim('last_name')) next.last_name = 'Please enter your last name.';
    if (!trim('username')) next.username = 'Please choose a username.';
  }

  if (step === 2) {
    const email = trim('email');
    if (!email) next.email = 'Please enter your email address.';
    else if (!EMAIL_PATTERN.test(email)) next.email = 'Please enter a valid email address.';

    const phone = trim('phone');
    if (phone && phone.replace(/\D/g, '').length < 10) {
      next.phone = 'Enter a valid phone number, or leave this blank.';
    }

    const birthYearRaw = trim('birth_year');
    if (birthYearRaw) {
      if (!/^\d{4}$/.test(birthYearRaw)) {
        next.birth_year = 'Use a four-digit year (e.g. 1990).';
      } else {
        const y = parseInt(birthYearRaw, 10);
        const current = new Date().getFullYear();
        if (y < 1900 || y > current) {
          next.birth_year = `Enter a year between 1900 and ${current}.`;
        }
      }
    }
  }

  if (step === 3) {
    const password = values.password ?? '';
    const pwError = validateStrongPassword(password);
    if (pwError) next.password = pwError;
    if (!values.termsAccepted) next.termsAccepted = 'You must accept the terms & conditions.';
  }

  return next;
}

const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [showPassword, setShowPassword] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const closeTerms = useCallback(() => setShowTermsModal(false), []);
  const { dialogRef: termsRef, initialRef: termsCloseRef } = useDialogFocus(showTermsModal, closeTerms);
  const [errors, setErrors] = useState({});
  const [values, setValues] = useState({
    username: '',
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    phone: '',
    birth_year: '',
    termsAccepted: false,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const val = type === 'checkbox' ? checked : value;
    setValues((prev) => ({ ...prev, [name]: val }));
    if (errors[name]) setErrors((prev) => { const next = { ...prev }; delete next[name]; return next; });
  };

  const handleNext = () => {
    const stepErrors = validateStep(step, values);
    if (Object.keys(stepErrors).length > 0) { setErrors(stepErrors); return; }
    setErrors({});
    setStep((s) => s + 1);
  };

  const handleBack = () => {
    setErrors({});
    setStep((s) => s - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const stepErrors = validateStep(3, values);
    if (Object.keys(stepErrors).length > 0) { setErrors(stepErrors); return; }
    setIsSubmitting(true);
    try {
      const birthRaw = values.birth_year?.trim() ?? '';
      await register({
        username: values.username.trim(),
        first_name: values.first_name.trim(),
        last_name: values.last_name.trim(),
        email: values.email.trim(),
        password: values.password,
        phone: values.phone?.trim() ?? '',
        birth_year: birthRaw === '' ? null : parseInt(birthRaw, 10),
      });
      navigate(ROUTES.LOGIN);
    } catch (err) {
      let errorMsg = 'Registration failed. Please try again.';
      if (err?.response?.data) {
        // Extract field-specific or general errors from the backend response
        const data = err.response.data;
        if (typeof data === 'string') {
          errorMsg = data;
        } else if (data.error) {
          errorMsg = data.error;
        } else if (data.detail) {
          errorMsg = data.detail;
        } else {
          // Flatten standard DRF field errors (e.g., {"username": ["This field must be unique."]})
          const messages = Object.entries(data).map(([field, msgs]) => {
            const fieldName = field.charAt(0).toUpperCase() + field.slice(1);
            return Array.isArray(msgs) ? `${fieldName}: ${msgs.join(' ')}` : `${fieldName}: ${msgs}`;
          });
          if (messages.length > 0) {
            errorMsg = messages.join(' | ');
          }
        }
      } else if (err?.message) {
        errorMsg = err.message;
      }
      setErrors({ general: errorMsg });
    } finally {
      setIsSubmitting(false);
    }
  };

  const { title, subtitle } = STEP_TITLES[step - 1];

  const passwordToggle = (
    <PasswordToggle shown={showPassword} onToggle={() => setShowPassword((prev) => !prev)} />
  );

  return (
    <AuthLayout>
      <AuthHeader icon={UserPlus} title={title} subtitle={subtitle} />

      <div className="mt-5 flex items-center justify-center gap-3">
        <StepIndicator currentStep={step} totalSteps={TOTAL_STEPS} />
        <span className="text-label text-text-muted">{step} / {TOTAL_STEPS}</span>
      </div>

      <Card as="section" padding="lg" className="mt-4">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
          {step === 1 && (
            <>
              <p className="text-center text-body text-text-muted">
                Enter your name and choose a username.
              </p>
              {/* cards-spec (05) section 4.3: the AI notice and the data link on step 1 */}
              <div data-testid="reg-ai-notice" className="rounded-2xl bg-surface-alt px-4 py-3 text-label text-text">
                <p>{REGISTRATION_STRINGS.en.notice}</p>
                <p dir="rtl" lang="ar" className="mt-1">{REGISTRATION_STRINGS.ar.notice}</p>
                <a
                  href={assetUrl(`${ROUTES.PRIVACY}?lang=en`)}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid="reg-privacy-link-1"
                  className="mt-2 inline-flex min-h-target items-center text-primary-strong underline"
                >
                  {REGISTRATION_STRINGS.en.dataLink}
                </a>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <AuthField
                  id="reg-first-name"
                  name="first_name"
                  label="First Name"
                  placeholder="First name"
                  value={values.first_name}
                  onChange={handleChange}
                  error={errors.first_name}
                  autoComplete="given-name"
                  required
                />
                <AuthField
                  id="reg-last-name"
                  name="last_name"
                  label="Last Name"
                  placeholder="Last name"
                  value={values.last_name}
                  onChange={handleChange}
                  error={errors.last_name}
                  autoComplete="family-name"
                  required
                />
              </div>
              <AuthField
                id="reg-username"
                name="username"
                label="Username"
                placeholder="Choose a username"
                value={values.username}
                onChange={handleChange}
                error={errors.username}
                autoComplete="username"
                required
              />
            </>
          )}

          {step === 2 && (
            <>
              <p className="text-center text-body text-text-muted">
                Your email is required. Phone and birth year are optional.
              </p>
              <AuthField
                id="reg-email"
                name="email"
                type="email"
                label="Email"
                placeholder="you@example.com"
                value={values.email}
                onChange={handleChange}
                error={errors.email}
                autoComplete="email"
                required
              />
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <AuthField
                  id="reg-phone"
                  name="phone"
                  type="tel"
                  label="Phone number"
                  placeholder="(555) 000-0000"
                  value={values.phone}
                  onChange={handleChange}
                  error={errors.phone}
                  autoComplete="tel"
                />
                <AuthField
                  id="reg-birth-year"
                  name="birth_year"
                  label="Birth year"
                  placeholder="e.g. 1990"
                  value={values.birth_year}
                  onChange={handleChange}
                  error={errors.birth_year}
                  inputMode="numeric"
                  autoComplete="bday-year"
                />
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <p className="text-center text-body text-text-muted">
                Create a strong password for your account.
              </p>
              <AuthField
                id="reg-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                label="Password"
                placeholder="Create a password"
                value={values.password}
                onChange={handleChange}
                error={errors.password}
                autoComplete="new-password"
                endAdornment={passwordToggle}
                hint="Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 symbol"
                required
              />
              <div className="flex items-start gap-3 px-1">
                <input
                  id="termsAccepted"
                  name="termsAccepted"
                  type="checkbox"
                  checked={values.termsAccepted}
                  onChange={handleChange}
                  aria-invalid={errors.termsAccepted ? true : undefined}
                  aria-describedby={errors.termsAccepted ? 'termsAccepted-error' : undefined}
                  className="mt-1 size-6 shrink-0 cursor-pointer accent-primary-strong"
                />
                <div className="flex flex-col">
                  <label htmlFor="termsAccepted" className="cursor-pointer select-none text-body text-text">
                    I agree to the{' '}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        setShowTermsModal(true);
                      }}
                      className="cursor-pointer text-primary-strong underline"
                    >
                      terms & conditions
                    </button>
                    {/* cards-spec (05): privacy policy link, new tab so the form is kept */}
                    {' '}and the{' '}
                    <a
                      href={assetUrl(`${ROUTES.PRIVACY}?lang=en`)}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid="reg-privacy-link-3"
                      className="text-primary-strong underline"
                    >
                      {REGISTRATION_STRINGS.en.privacyPolicy}
                    </a>
                  </label>
                  {errors.termsAccepted && (
                    <p id="termsAccepted-error" className="mt-1 text-label text-danger-strong">
                      {errors.termsAccepted}
                    </p>
                  )}
                </div>
              </div>
              {errors.general && (
                <div className="rounded-2xl bg-danger-soft p-3" role="alert">
                  <p className="text-label text-danger-strong">{errors.general}</p>
                </div>
              )}
            </>
          )}

          <div className={`flex gap-3 ${step > 1 ? 'flex-row' : 'flex-col'}`}>
            {step > 1 && (
              <Button
                variant="secondary"
                onClick={handleBack}
                className="flex-1"
                icon={<ArrowLeft aria-hidden="true" className="size-5 rtl:rotate-180" />}
              >
                Back
              </Button>
            )}

            {step < TOTAL_STEPS ? (
              <Button key="next" onClick={handleNext} className="flex-1">
                Next
                <ArrowRight aria-hidden="true" className="size-5 rtl:rotate-180" />
              </Button>
            ) : (
              <Button
                key="submit"
                type="submit"
                loading={isSubmitting}
                className="flex-1"
                icon={isSubmitting ? null : <UserPlus aria-hidden="true" className="size-5" />}
              >
                {isSubmitting ? 'Creating account...' : 'Create Account'}
              </Button>
            )}
          </div>

          {step === 1 && (
            <ButtonLink to={ROUTES.LOGIN}>Already have an account? Login</ButtonLink>
          )}
        </form>
      </Card>

      <p className="mt-5 text-center text-label text-text-muted">
        Parent-controlled setup • Child-safe access
      </p>

      {/* Terms Modal */}
      {showTermsModal && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4"
          onClick={closeTerms}
        >
          <div
            ref={termsRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="terms-title"
            className="relative flex h-[75vh] w-full max-w-md flex-col overflow-hidden rounded-3xl border border-border bg-surface p-6 text-text sm:h-[500px]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="absolute end-2 top-2">
              <IconButton
                ref={termsCloseRef}
                label="Close terms modal"
                variant="ghost"
                onClick={closeTerms}
                icon={<X aria-hidden="true" className="size-5" />}
              />
            </div>

            <h2 id="terms-title" className="mb-4 shrink-0 pe-14 text-heading text-text">Terms & Conditions</h2>
            <div className="flex-1 space-y-4 overflow-y-auto pe-2 text-body text-text">
              <p>
                <strong>1. Acceptance of Terms</strong><br />
                By creating an account, accessing, or using the Alsadiq-Alsadouq platform, you agree to be bound by these terms and conditions. If you do not agree with any part of these terms, you may not access our services.
              </p>
              <p>
                <strong>2. User Responsibilities</strong><br />
                You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account. We will not be liable for any loss or damage arising from your failure to comply with this security obligation.
              </p>
              <p>
                <strong>3. Privacy & Data Collection</strong><br />
                We respect your privacy and are committed to protecting it. Our data collection and use policies are described in our{' '}
                <a
                  href={assetUrl(`${ROUTES.PRIVACY}?lang=en`)}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid="terms-privacy-link"
                  className="text-primary-strong underline"
                >
                  Privacy Policy
                </a>
                , which is incorporated into these terms. We implement reasonable security measures to protect against unauthorized access to our systems, ensuring a child-safe environment.
              </p>
              <p>
                <strong>4. Acceptable Use Policy</strong><br />
                Users must not use the platform to transmit any content that is illegal, harmful, threatening, abusive, harassing, defamatory, vulgar, obscene, invasive of another's privacy, hateful, or racially, ethnically, or otherwise objectionable. Parents are responsible for monitoring their children's use of the application.
              </p>
              <p>
                <strong>5. Intellectual Property Rights</strong><br />
                All content, features, and functionality on the platform, including but not limited to text, graphics, logos, icons, audio clips, and software, are the exclusive property of Alsadiq-Alsadouq or its licensors and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.
              </p>
              <p>
                <strong>6. Service Modifications and Availability</strong><br />
                We reserve the right to withdraw or amend this platform, and any service or material we provide, in our sole discretion without notice. We will not be liable if, for any reason, all or any part of the platform is unavailable at any time or for any period.
              </p>
              <p>
                <strong>7. Limitation of Liability</strong><br />
                In no event will Alsadiq-Alsadouq, its affiliates, or their licensors, service providers, employees, agents, officers, or directors be liable for damages of any kind, under any legal theory, arising out of or in connection with your use, or inability to use, the platform.
              </p>
              <p>
                <strong>8. Governing Law and Jurisdiction</strong><br />
                All matters relating to the platform and these Terms of Use, and any dispute or claim arising therefrom or related thereto, shall be governed by and construed in accordance with the internal laws of the jurisdiction in which the company operates, without giving effect to any choice or conflict of law provision or rule.
              </p>
              <p>
                <strong>9. Account Termination</strong><br />
                We reserve the right to suspend or terminate accounts that violate these terms, engage in inappropriate behavior, or remain inactive for an extended period of time, without prior notice or liability.
              </p>
              <p>
                <strong>10. Modifications to the Terms</strong><br />
                We may revise and update these Terms of Use from time to time in our sole discretion. All changes are effective immediately when we post them. Your continued use of the platform following the posting of revised Terms of Use means that you accept and agree to the changes.
              </p>
              {/* cards-spec (05) section 4.3: clause 11 */}
              {/* cards-spec (05) review: the bold heading is "11. AI Companion", like the other clause headings */}
              <p data-testid="terms-clause-11">
                <strong>{clauseParts(REGISTRATION_STRINGS.en.terms11)[0]}</strong><br />
                {clauseParts(REGISTRATION_STRINGS.en.terms11)[1]}
              </p>
              <p dir="rtl" lang="ar">
                <strong>{clauseParts(REGISTRATION_STRINGS.ar.terms11)[0]}</strong><br />
                {clauseParts(REGISTRATION_STRINGS.ar.terms11)[1]}
              </p>
            </div>

            <div className="mt-6 flex shrink-0 flex-col justify-end gap-3 border-t border-border pt-4 sm:flex-row">
              <Button variant="secondary" onClick={closeTerms}>
                Close
              </Button>
              <Button
                onClick={() => {
                  setValues(prev => ({ ...prev, termsAccepted: true }));
                  setErrors(prev => { const next = { ...prev }; delete next.termsAccepted; return next; });
                  setShowTermsModal(false);
                }}
              >
                Accept & Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </AuthLayout>
  );
};

export default Register;
