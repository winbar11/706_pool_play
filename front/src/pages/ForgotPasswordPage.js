import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../utils/api";
import logo from "../static/usa706.webp";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.auth.forgotPassword(email.trim());
      setSubmitted(true);
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
          <img src={logo} alt="706 Pool Play" height="150" style={{ objectFit: "contain" }} />
        </div>

        <h2>Reset Password</h2>

        {submitted ? (
          <div>
            <div className="alert alert-success">
              If that email is registered, you'll receive a reset link shortly. Check your inbox.
            </div>
            <p className="text-center mt-2" style={{ fontSize: "0.85rem", color: "var(--green-300)" }}>
              <Link to="/login" style={{ color: "var(--gold-300)", textDecoration: "none" }}>
                ← Back to sign in
              </Link>
            </p>
          </div>
        ) : (
          <>
            <p style={{ fontSize: "0.9rem", color: "var(--green-300)", marginBottom: "1rem" }}>
              Enter the email address on your account and we'll send you a reset link.
            </p>

            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={submit}>
              <div className="form-group">
                <label>Email address</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
              </div>
              <button className="btn btn-primary btn-full mt-2" disabled={loading}>
                {loading ? "Sending…" : "Send Reset Link"}
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
