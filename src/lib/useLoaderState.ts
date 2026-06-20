import { useEffect, useState } from 'react';
import { getState, subscribe, type LoaderState } from '../data/loader';

export { getState, subscribe, loadQuestions } from '../data/loader';
export type { LoaderState } from '../data/loader';

/**
 * React hook that subscribes to the global loader state and re-renders
 * the consuming component when the question bank is loaded/updated.
 * Replaces the previous `tick` + `eslint-disable` pattern.
 */
export function useLoaderState(): LoaderState {
  const [state, setState] = useState<LoaderState>(getState);
  useEffect(() => subscribe(() => setState(getState())), []);
  return state;
}
