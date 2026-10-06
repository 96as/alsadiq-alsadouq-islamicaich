export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password/:uid/:token',
  /** cards-spec (05): public, outside every guard. */
  PRIVACY: '/privacy',
  CHILD_HOME: '/child',
  CHILD_QUESTS: '/child/quests',
  CHILD_BADGES: '/child/badges',
  CHILD_SETTINGS: '/child/settings',
  PARENT_HOME: '/parent',
  /** Parent: stories & summaries (replaces old quests tab). */
  PARENT_INSIGHTS: '/parent/insights',
  PARENT_ALERTS: '/parent/alerts',
  PARENT_SETTINGS: '/parent/settings',
};

/** @param {string|number} childId */
export const parentChildSummaryPath = (childId) => `/parent/children/${childId}/summary`;
