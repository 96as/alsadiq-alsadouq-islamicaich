export const hasProgress = (b) => typeof b.progressCurrent === 'number' && b.requirementValue > 0;
