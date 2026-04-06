import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../static/706_pool_logo.svg";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", phone: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("Passwords don't match");
      return;
    }
    setLoading(true);
    try {
      await register(form.username, form.email, form.password, form.phone || null);
      navigate("/draft");
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
          <img src={logo} alt="706 Masters Pool" height="150" style={{ objectFit: "contain" }} />
        </div>

        <h2>Create account</h2>
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={submit}>
          <div className="form-group">
            <label>Username</label>
            <input name="username" value={form.username} onChange={handle}
              placeholder="choose a username" required minLength={3} />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input name="email" type="email" value={form.email} onChange={handle}
              placeholder="you@example.com" required />
          </div>
          <div className="form-group">
            <label>Phone number <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>(for payment tracking)</span></label>
            <input name="phone" type="tel" value={form.phone} onChange={handle}
              placeholder="(555) 555-5555" />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input name="password" type="password" value={form.password}
              onChange={handle} placeholder="min 6 characters" required minLength={6} />
          </div>
          <div className="form-group">
            <label>Confirm password</label>
            <input name="confirm" type="password" value={form.confirm}
              onChange={handle} placeholder="repeat password" required />
          </div>
          <button className="btn btn-primary btn-full mt-2" disabled={loading}>
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-center mt-2" style={{ fontSize: "0.85rem", color: "var(--green-300)" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "var(--gold-300)", textDecoration: "none" }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}