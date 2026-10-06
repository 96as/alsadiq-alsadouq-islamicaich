import { createContext, useContext } from 'react';

/** Holds the runtime object from runtime.js for every component inside the canvas. */
export const ForestCtx = createContext(null);

export function useForest() {
  const rt = useContext(ForestCtx);
  if (!rt) throw new Error('useForest must be used inside a forest scene');
  return rt;
}
