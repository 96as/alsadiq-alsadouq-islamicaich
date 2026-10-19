import { BookOpen, Moon, Lightbulb, Bird, TreePine, Star } from 'lucide-react';

/**
 * Keys must match backend CHILD_PROFILE_ICON_CHOICES.
 * Icons and labels are UI-only — the stored value (sparkles, star, etc.) is what the backend uses.
 */
export const PROFILE_ICON_OPTIONS = [
  { value: 'sparkles',  label: 'Wonder',     Icon: Lightbulb },
  { value: 'star',      label: 'Achievement', Icon: Star      },
  { value: 'heart',     label: 'Gratitude',   Icon: Bird      },
  { value: 'smile',     label: 'Knowledge',   Icon: BookOpen  },
  { value: 'cat',       label: 'Faith',       Icon: Moon      },
  { value: 'rainbow',   label: 'Growth',      Icon: TreePine  },
];

export function getProfileIconComponent(value) {
  const found = PROFILE_ICON_OPTIONS.find((o) => o.value === value);
  return found?.Icon ?? Lightbulb;
}
