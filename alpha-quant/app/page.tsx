'use client';

import React, { useState, useEffect } from 'react';
import NavigationBar from '@/components/layout/NavigationBar';
import LoginScreen from '@/components/LoginScreen';
import ErrorBoundary from '@/components/ErrorBoundary';
import DashboardPage from '@/components/pages/DashboardPage';
import ChartPage from '@/components/pages/ChartPage';
import AnalyticsPage from '@/components/pages/AnalyticsPage';
import HistoryPage from '@/components/pages/HistoryPage';
import SettingsPage from '@/components/pages/SettingsPage';
import { apiService } from '@/lib/api';

export default function Home() {
  // Check auth synchronously from localStorage to prevent flash
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    if (typeof window !== 'undefined') {
      return !!localStorage.getItem('token');
    }
    return false;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isEngineRunning, setIsEngineRunning] = useState(false);
  const [statusData, setStatusData] = useState<any>(null);

  useEffect(() => {
    // Mark as loaded after initial render
    setIsLoading(false);

    // Polling Status (2s - balanced performance)
    const poll = setInterval(fetchStatus, 2000);
    return () => clearInterval(poll);
  }, []);

  const fetchStatus = async () => {
    try {
      // Only fetch if we have a token (or if API handles 401 gracefully, which we configured)
      const token = localStorage.getItem('token');
      if (!token) return;

      const res = await apiService.get('/status');
      // Backend returns StatusResponse directly
      if (res.data) {
        setIsEngineRunning(res.data.running);
        setStatusData(res.data);
      }
    } catch (e) {
      // console.error("Poll Error", e);
    }
  };

  const toggleEngine = async (running: boolean) => {
    try {
      await apiService.post(running ? '/start' : '/stop', {});
      setIsEngineRunning(running);
      fetchStatus();
    } catch (e: any) {
      alert(e.response?.data?.message || 'Command Failed');
    }
  };

  // Show loading spinner during initial auth check (prevents flash)
  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#000000]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/30"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-background text-white selection:bg-primary/30">

      {/* Content Area with Error Boundary */}
      <div className="absolute inset-0 pb-20">
        <ErrorBoundary>
          {activeTab === 'dashboard' && (
            <DashboardPage
              isEngineRunning={isEngineRunning}
              toggleEngine={toggleEngine}
              statusData={statusData}
              refreshStatus={fetchStatus}
            />
          )}
          {activeTab === 'chart' && <ChartPage statusData={statusData} />}
          {activeTab === 'analytics' && <AnalyticsPage isEngineRunning={isEngineRunning} />}
          {activeTab === 'history' && <HistoryPage />}
          {activeTab === 'settings' && <SettingsPage />}
        </ErrorBoundary>
      </div>

      {/* Navigation Dock */}
      <NavigationBar activeTab={activeTab} onSwitch={setActiveTab} />
    </main>
  );
}
