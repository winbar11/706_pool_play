import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.username, form.password);
      navigate("/");
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
          <div className="flag">⛳</div>
          <h1>Masters 706 Pool</h1>
          <p>2026</p>
        </div>

        <h2>Sign in</h2>
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={submit}>
          <div className="form-group">
            <label>Username</label>
            <input name="username" value={form.username} onChange={handle}
              placeholder="your username" autoComplete="username" required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input name="password" type="password" value={form.password}
              onChange={handle} placeholder="••••••••" autoComplete="current-password" required />
          </div>
          <button className="btn btn-primary btn-full mt-2" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-center mt-2" style={{ fontSize: "0.85rem", color: "var(--green-300)" }}>
          No account?{" "}
          <Link to="/register" style={{ color: "var(--gold-300)", textDecoration: "none" }}>
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}