import React from 'react';
import { AuthProvider, useAuth } from './AuthContext';
import LoginPage from './LoginPage';
import Dashboard from './Dashboard';
import './index.css';

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-pulse"></div>
        <p>TVK CONNECT</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="dashboard-layout">
      <Dashboard />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
