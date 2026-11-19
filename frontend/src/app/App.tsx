import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../context/AuthProvider';
import { AppShell } from '../components/layout/AppShell';
import { OverviewPage } from '../features/overview/OverviewPage';
import { SalesPage } from '../features/sales/SalesPage';
import { CustomersPage } from '../features/customers/CustomersPage';
import { MarketingPage } from '../features/marketing/MarketingPage';
import { FinancePage } from '../features/finance/FinancePage';
import { InventoryPage } from '../features/inventory/InventoryPage';
import { OperationsPage } from '../features/operations/OperationsPage';
import { SuppliersPage } from '../features/suppliers/SuppliersPage';
import { StatisticsPage } from '../features/statistics/StatisticsPage';
import { PredictionsPage } from '../features/predictions/PredictionsPage';
import { AnomaliesPage } from '../features/anomalies/AnomaliesPage';
import { ReportsPage } from '../features/reports/ReportsPage';
import { DataSourcesPage } from '../features/data-sources/DataSourcesPage';
import { DataQualityPage } from '../features/data-quality/DataQualityPage';
import { AdminPage } from '../features/administration/AdminPage';
import '../styles/theme.css';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<OverviewPage />} />
            <Route path="sales" element={<SalesPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="marketing" element={<MarketingPage />} />
            <Route path="finance" element={<FinancePage />} />
            <Route path="inventory" element={<InventoryPage />} />
            <Route path="operations" element={<OperationsPage />} />
            <Route path="suppliers" element={<SuppliersPage />} />
            <Route path="statistics" element={<StatisticsPage />} />
            <Route path="predictions" element={<PredictionsPage />} />
            <Route path="anomalies" element={<AnomaliesPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="data-sources" element={<DataSourcesPage />} />
            <Route path="data-quality" element={<DataQualityPage />} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
