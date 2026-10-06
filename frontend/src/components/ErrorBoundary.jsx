import { Component } from 'react';
import { Button } from './ui';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          data-theme="parent"
          className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto bg-bg p-6 text-text"
        >
          <div className="flex flex-col items-center gap-3 text-center">
            <p className="text-display text-primary-strong" aria-hidden="true">Oops</p>
            <h1 className="text-title text-text">Something went wrong</h1>
            <p className="text-body text-text-muted">Try refreshing the page.</p>
            <Button className="mt-3" onClick={() => window.location.reload()}>
              Refresh
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
