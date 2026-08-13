import React, { useState } from "react";
import { loginUser, registerUser } from "../services/auth.js";

export default function AuthPage({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !password.trim()) {
      setError("Please fill in all fields.");
      return;
    }
    try {
      let user;
      if (isRegister) {
        user = registerUser(username.trim(), password);
      } else {
        user = loginUser(username.trim(), password);
      }
      onLoginSuccess(user);
    } catch (err) {
      setError(err.message || "Authentication failed.");
    }
  }

  return (
    <div className="auth-page-container">
      <div className="hero" style={{ marginBottom: 32 }}>
        <div className="hero-badge">⚖️ AI-Powered Comparator</div>
        <h1>
          Find the <span className="gradient-text">Best Deal</span>
        </h1>
        <p style={{ fontSize: 15, maxWidth: 460 }}>
          Compare prices, customer reviews, seller quality, warranty, and condition. Sign in to start comparing.
        </p>
      </div>

      <div className="card auth-card glow">
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${!isRegister ? "active" : ""}`}
            onClick={() => { setIsRegister(false); setError(null); }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${isRegister ? "active" : ""}`}
            onClick={() => { setIsRegister(true); setError(null); }}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ marginTop: 24 }}>
          {error && (
            <div className="form-error" style={{ marginBottom: 16 }}>
              <span>⚠️</span> {error}
            </div>
          )}

          <div className="auth-input-group">
            <label htmlFor="auth-username">Username</label>
            <input
              id="auth-username"
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>

          <div className="auth-input-group" style={{ marginTop: 16 }}>
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="compare-btn" style={{ marginTop: 28 }}>
            {isRegister ? "Create Account & Sign In" : "Sign In"}
          </button>
        </form>

        <div className="auth-footer">
          {isRegister ? (
            <span>Already have an account? <button className="auth-link-btn" onClick={() => setIsRegister(false)}>Sign In</button></span>
          ) : (
            <span>New here? <button className="auth-link-btn" onClick={() => setIsRegister(true)}>Create Account</button></span>
          )}
        </div>
      </div>
    </div>
  );
}
