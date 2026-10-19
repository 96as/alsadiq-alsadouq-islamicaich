/** Icon + title + subtitle block shown above each auth form. */
const AuthHeader = ({ icon, title, subtitle }) => {
  const Icon = icon;
  return (
    <header className="flex flex-col items-center gap-2 text-center">
      <span
        className="flex size-18 items-center justify-center rounded-4xl bg-primary-soft text-primary-strong"
        aria-hidden="true"
      >
        <Icon className="size-8" />
      </span>
      <h1 className="text-title text-text">{title}</h1>
      {subtitle ? <p className="text-body text-text-muted">{subtitle}</p> : null}
    </header>
  );
};

export default AuthHeader;
