import React, { useState, useEffect } from "react";
import Home from "./pages/Home.jsx";
import Results from "./pages/Results.jsx";
import HistoryPanel from "./components/HistoryPanel.jsx";
import AuthPage from "./components/AuthPage.jsx";
import { saveComparison } from "./services/history.js";
import { getCurrentUser, logoutUser } from "./services/auth.js";

export default function App() {
  const [result, setResult] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [user, setUser] = useState(() => getCurrentUser());

  // Sync theme to root html element
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  };

  const handleResult = (newResult) => {
    setResult(newResult);
    saveComparison(newResult);
  };

  const handleRestore = (restoredResult) => {
    setResult(restoredResult);
  };

  const handleReset = () => setResult(null);

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    handleReset();
  };

  const handleLogout = () => {
    logoutUser();
    setUser(null);
    handleReset();
    setIsHistoryOpen(false);
  };

  return (
    <div className="app-shell">
      <nav className="top-nav">
        <div className="nav-inner">
          <div className="brand" onClick={handleReset}>
            <div className="brand-logo">⚖️</div>
            <span>AI Product Comparator</span>
          </div>

          <div className="nav-actions">
            <button className="nav-btn" onClick={toggleTheme} title="Toggle theme">
              {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
            </button>

            {user && (
              <>
                <span className="user-profile-badge">👋 {user.username}</span>
                <button
                  className={`nav-btn ${isHistoryOpen ? "active" : ""}`}
                  onClick={() => setIsHistoryOpen(true)}
                  title="View History"
                >
                  🕐 History
                </button>
                <button className="nav-btn logout-btn" onClick={handleLogout} title="Log Out">
                  🚪 Log Out
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="main-content">
        {!user ? (
          <AuthPage onLoginSuccess={handleLoginSuccess} />
        ) : result ? (
          <Results result={result} onReset={handleReset} />
        ) : (
          <Home onResult={handleResult} />
        )}
      </main>

      {isHistoryOpen && user && (
        <HistoryPanel
          onClose={() => setIsHistoryOpen(false)}
          onRestore={handleRestore}
        />
      )}
    </div>
  );
}
