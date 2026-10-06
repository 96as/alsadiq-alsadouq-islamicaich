import { Link } from 'react-router-dom';
import { cx, FOCUS_RING } from '../../../components/ui/cx';

const VARIANTS = {
  primary: 'bg-primary text-on-primary',
  secondary: 'bg-primary-soft text-text',
};

/** Router Link styled like the lg Button. variant: 'primary' | 'secondary'. */
const ButtonLink = ({ variant = 'secondary', className = '', children, ...rest }) => (
  <Link
    className={cx(
      'inline-flex min-h-target w-full items-center justify-center gap-2 rounded-3xl px-5 text-heading',
      FOCUS_RING,
      VARIANTS[variant],
      className,
    )}
    {...rest}
  >
    {children}
  </Link>
);

export default ButtonLink;
