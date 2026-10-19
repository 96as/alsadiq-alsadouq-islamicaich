import { Component } from 'react';

/**
 * Tiny error boundary for the forest. A failure anywhere below it (model
 * download, WebGL context, shader) calls onError once and renders `fallback`.
 */
export default class ForestBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    if (typeof this.props.onError === 'function') this.props.onError(error);
  }

  render() {
    if (this.state.failed) return this.props.fallback ?? null;
    return this.props.children;
  }
}
