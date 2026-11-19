import { ReactNode } from 'react';

export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: ReactNode;
  badge?: string;
  requiredPermission?: string;
  ownerOnly?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
}
