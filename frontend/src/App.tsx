import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CustomThemeProvider } from './context/ThemeContext';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ScraperPage } from './pages/ScraperPage';
import { JobsPage } from './pages/JobsPage';
import { CompaniesPage } from './pages/CompaniesPage';
import { ExportPage } from './pages/ExportPage';
import { LogsPage } from './pages/LogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { MarketingPage } from './pages/MarketingPage';


const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Auth state is advisory only — the StartupTN session is required for
  // scraping, but not for viewing dashboard, companies, jobs, export or logs.
  // All data pages are accessible without a StartupTN session.
  return <>{children}</>;
};


export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <CustomThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <AuthGuard>
                  <Layout />
                </AuthGuard>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="scraper" element={<ScraperPage />} />
              <Route path="jobs" element={<JobsPage />} />
              <Route path="companies" element={<CompaniesPage />} />
              <Route path="marketing" element={<MarketingPage />} />
              <Route path="export" element={<ExportPage />} />
              <Route path="logs" element={<LogsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </CustomThemeProvider>
    </QueryClientProvider>
  );
};
