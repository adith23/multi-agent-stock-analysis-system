"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

import { ActionButton } from "./action-button";

interface FeatureErrorBoundaryProps {
  children: ReactNode;
  resetKey: string;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface FeatureErrorBoundaryState {
  error: Error | null;
}

export class FeatureErrorBoundary extends Component<FeatureErrorBoundaryProps, FeatureErrorBoundaryState> {
  state: FeatureErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): FeatureErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.props.onError?.(error, errorInfo);
  }

  componentDidUpdate(previousProps: FeatureErrorBoundaryProps): void {
    if (previousProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render(): ReactNode {
    if (!this.state.error) return this.props.children;

    return (
      <div className="grid min-h-64 place-items-center border border-red/40 bg-red/5 p-6" role="alert">
        <div className="max-w-md text-center">
          <AlertTriangle className="mx-auto size-6 text-red" aria-hidden="true" />
          <h2 className="mt-3 font-serif text-lg">This workspace panel could not be rendered</h2>
          <p className="mt-2 text-xs leading-relaxed text-text-dim">
            The rest of the terminal is still available. Retry this panel or choose another view.
          </p>
          <ActionButton className="mt-4" color="var(--color-red)" onClick={() => this.setState({ error: null })}>
            <RefreshCw className="mr-1 size-3" aria-hidden="true" />Retry panel
          </ActionButton>
        </div>
      </div>
    );
  }
}
