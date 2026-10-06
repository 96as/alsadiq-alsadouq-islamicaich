/**
 * Static badge artwork (see /public/badges/*.png).
 * Extend when new badge art is added.
 */
import { assetUrl } from '../../../utils/assetUrl';

const NORMALIZE = (s) =>
  s
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/[–—-]/g, '-');

/** @type {Record<string, string>} slug -> public URL */
const BADGE_SRC = {
  'first value practised': assetUrl('/badges/honesty-seed.png'),
  'good listener': assetUrl('/badges/good-listener.png'),
  '3-day streak': assetUrl('/badges/three-day-streak.png'),
  '3 day streak': assetUrl('/badges/three-day-streak.png'),
};

/**
 * @param {string} label — badge title as shown in UI
 * @returns {string | null} image URL or null for text-only badges
 */
export function badgeImageUrlForLabel(label) {
  const key = NORMALIZE(label);
  return BADGE_SRC[key] ?? null;
}
