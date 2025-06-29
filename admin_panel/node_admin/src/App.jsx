import React, { useState, useEffect } from "react";
import SystemResources from "./components/SystemResources";
import ServiceStatus from "./components/ServiceStatus";
import PerformanceMetrics from "./components/PerformanceMetrics";
import ActiveTasks from "./components/ActiveTasks";
import VideoStatus from "./components/VideoStatus";
import StorageInfo from "./components/StorageInfo";
import ConfigPanel from "./components/ConfigPanel";
import ManualCleanup from "./components/ManualCleanup";
import "./App.css";

const THEME_KEY = "admin_theme";

function getInitialTheme() {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved) return saved;
    // Prefer system dark mode
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "theme-dark";
    }
  }
  return "theme-light";
}

function StarsBackground() {
  // Simple animated stars using CSS
  return <div className="stars-bg"></div>;
}

export default function App() {
  const [theme, setTheme] = useState(getInitialTheme());

  useEffect(() => {
    document.body.classList.remove("theme-light", "theme-dark");
    document.body.classList.add(theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((t) => (t === "theme-light" ? "theme-dark" : "theme-light"));
  };

  return (
    <div className={theme}>
      <StarsBackground />
      <header className="header-bar">
        <div className="header-title">
          <span className="widget-icon" role="img" aria-label="Rocket">🚀</span>
          Video Admin Panel
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          <button className="theme-toggle" onClick={toggleTheme} title="Tema Değiştir">
            {theme === "theme-light" ? (
              <span role="img" aria-label="Dark Mode">🌙</span>
            ) : (
              <span role="img" aria-label="Light Mode">☀️</span>
            )}
          </button>
        </div>
      </header>
      <main>
        <div className="dashboard-grid">
          <SystemResources />
          <PerformanceMetrics />
          <StorageInfo />
          <ServiceStatus />
          <ManualCleanup />
          <ConfigPanel />
          <ActiveTasks />
          <div className="video-status-full"><VideoStatus /></div>
        </div>
      </main>
      <footer className="text-center" style={{marginTop: '2.5rem', color: '#bda4e6', fontSize: '1rem'}}>
        &copy; {new Date().getFullYear()} Video Admin Panel &mdash; Made with TGDeity 🚀 | TGDeity 2025
      </footer>
    </div>
  );
} 