export type PageId =
  | 'overview'
  | 'claims-intelligence'
  | 'provider-risk'
  | 'investigation-queue'
  | 'model-insights'
  | 'data-management'
  | 'settings';

export interface NavigationItem {
  id: PageId;
  label: string;
  description: string;
  badge?: string;
}
