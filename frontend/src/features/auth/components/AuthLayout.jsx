/**
 * AuthLayout: full-screen wrapper for the public auth pages.
 * Uses the warm child palette, like the mobile auth screens (the mobile theme
 * role defaults to 'child' until a user is signed in). The old stars/intro
 * animation was removed because it clashed with the light theme.
 */
const AuthLayout = ({ children }) => (
  <div
    className="relative flex min-h-0 flex-1 flex-col items-center overflow-y-auto bg-bg p-4 text-text antialiased sm:p-6"
    data-theme="child"
    data-view="auth"
  >
    <main className="my-auto w-full max-w-xl py-6">{children}</main>
  </div>
);

export default AuthLayout;
