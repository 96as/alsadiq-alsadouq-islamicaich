import { useEffect, useState, useSyncExternalStore } from 'react';
import { timeOfDayFromDate } from '../child/components/forest/timeOfDay';

/** A CSS media query as a boolean that follows changes (reduced motion, pointer type, orientation). */
export function useMedia(query) {
  return useSyncExternalStore(
    (notify) => {
      const mq = window.matchMedia(query);
      mq.addEventListener('change', notify);
      return () => mq.removeEventListener('change', notify);
    },
    () => window.matchMedia(query).matches,
    () => false,
  );
}

export const useReducedMotion = () => useMedia('(prefers-reduced-motion: reduce)');

/** The landing's time of day, from the device clock (the same rule the forest uses), checked every minute. */
export function useClockPeriod() {
  const [name, setName] = useState(() => timeOfDayFromDate());
  useEffect(() => {
    const id = window.setInterval(() => setName(timeOfDayFromDate()), 60000);
    return () => window.clearInterval(id);
  }, []);
  return name;
}
