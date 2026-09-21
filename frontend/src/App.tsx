import React from 'react';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';

export default function App() {
  return (
    <div className="min-h-screen bg-navy-900 text-slate-100">
      <Header />
      <Dashboard />
    </div>
  );
}
