import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../utils/api";
import { useTheme } from "../hooks/useTheme.js";
import logo from "../static/usa706.webp";
import logoOpenChampionship from "../static/usa706-open-championship.png";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const theme = useTheme();
  const logoSrc = theme === "open-championship" ? logoOpenChampionship : logo;

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    try {
      await api.auth.resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <img src={logoSrc} alt="706 Pool Play" height="150" style={{ objectFit: "contain" }} />
        </div>

        <h2>Choose New Password</h2>

        {!token && (
          <div className="alert alert-error">
            Missing reset token. Please use the link from your email.
          </div>
        )}

        {done ? (
          <div>
            <div className="alert alert-success">
              Your password has been updated. You can now sign in.
            </div>
            <Link to="/login" className="btn btn-primary btn-full mt-2"
              style={{ display: "block", textAlign: "center" }}>
              Sign in →
            </Link>
          </div>
        ) : (
          <>
            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={submit}>
              <div className="form-group">
                <label>New password</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  autoComplete="new-password"
                  required
                  disabled={!token}
                />
              </div>
              <div className="form-group">
                <label>Confirm password</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  placeholder="Repeat your new password"
                  autoComplete="new-password"
                  required
                  disabled={!token}
                />
              </div>
              <button className="btn btn-primary btn-full mt-2"
                disabled={loading || !token}>
                {loading ? "Saving…" : "Set New Password"}
              </button>
            </form>

            <p className="text-center mt-2" style={{ fontSize: "0.85rem", color: "var(--green-300)" }}>
              <Link to="/login" style={{ color: "var(--gold-300)", textDecoration: "none" }}>
                ← Back to sign in
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
