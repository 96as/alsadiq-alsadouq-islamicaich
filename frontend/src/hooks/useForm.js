import { useState } from 'react';

const formatApiMessage = (val) => {
    if (Array.isArray(val)) return val.map(String).join(' ');
    return String(val);
};

/**
 * Reusable form state hook.
 *
 * @param {Object}   options
 * @param {Object}   options.initialValues  - { fieldName: defaultValue }
 * @param {Function} options.onSubmit       - async (values) => {} called on valid submit
 * @param {Function} [options.validate]     - (values) => ({ fieldName: message }) client-side errors; empty object if valid
 * @returns {{ values, errors, handleChange, handleSubmit, isSubmitting, setErrors, resetForm }}
 */
const useForm = ({ initialValues, onSubmit, validate }) => {
    const [values, setValues] = useState(initialValues);
    const [errors, setErrors] = useState({});
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Updates the matching field in values when an input changes.
    // Works with any <input name="fieldName" /> — the `name` attr is the key.
    const handleChange = (e) => {
        const { name, value } = e.target;
        setValues((prev) => ({ ...prev, [name]: value }));

        setErrors((prev) => {
            if (!prev[name] && !prev.general) return prev;
            const next = { ...prev };
            if (name && next[name]) delete next[name];
            if (next.general) delete next.general;
            return Object.keys(next).length ? next : {};
        });
    };

    // Wraps the onSubmit callback with loading state + error handling.
    // Catches API errors and puts them in errors.general for display.
    const handleSubmit = async (e) => {
        e.preventDefault();
        setErrors({});

        if (typeof validate === 'function') {
            const validationErrors = validate(values) || {};
            if (Object.keys(validationErrors).length > 0) {
                setErrors(validationErrors);
                return;
            }
        }

        setIsSubmitting(true);

        try {
            await onSubmit(values);
        } catch (err) {
            // Django REST Framework returns errors in different shapes:
            // - { detail: "..." } for auth errors
            // - { field_name: ["error"] } for validation errors
            // - { non_field_errors: [...] }
            const status = err.response?.status;
            const apiErrors = err.response?.data;

            if (apiErrors) {
                if (typeof apiErrors === 'string') {
                    setErrors({ general: apiErrors });
                } else if (apiErrors.detail != null) {
                    setErrors({ general: formatApiMessage(apiErrors.detail) });
                } else if (apiErrors.non_field_errors != null) {
                    setErrors({ general: formatApiMessage(apiErrors.non_field_errors) });
                } else {
                    const fieldErrors = {};
                    Object.entries(apiErrors).forEach(([key, val]) => {
                        if (key === 'non_field_errors') return;
                        fieldErrors[key] = formatApiMessage(val);
                    });
                    setErrors(fieldErrors);
                }
            } else if (
                !err.response
                && (err.code === 'ERR_NETWORK'
                    || err.message?.toLowerCase().includes('network'))
            ) {
                setErrors({
                    general: 'Unable to reach the server. Check your connection and try again.',
                });
            } else if (status >= 500) {
                setErrors({
                    general: 'The server is having trouble. Please try again in a moment.',
                });
            } else {
                setErrors({ general: 'Something went wrong. Please try again.' });
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    // Reset form to initial state
    const resetForm = () => {
        setValues(initialValues);
        setErrors({});
    };

    return { values, errors, handleChange, handleSubmit, isSubmitting, setErrors, resetForm };
};

export default useForm;
