import { stringsFor } from '../i18n/stringsFor.js'; // i18n

/** `lang` is optional: pages that are not localised yet keep their English messages. */
export function validateStrongPassword(password, lang = 'en') {
  const v = stringsFor(lang).validation;
  if (!password) return v.passwordRequired;
  if (password.length < 8) return v.passwordShort;
  if (!/[A-Z]/.test(password)) return v.passwordUpper;
  if (!/[a-z]/.test(password)) return v.passwordLower;
  if (!/[0-9]/.test(password)) return v.passwordNumber;
  if (!/[^A-Za-z0-9]/.test(password)) {
    return v.passwordSymbol;
  }
  return null;
}
