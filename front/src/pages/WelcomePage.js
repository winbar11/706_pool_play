import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../static/706_pool_logo.svg";

export default function WelcomePage() {
  const { user } = useAuth() ?? {};

  return (
    <div>
<div className="page-header" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <img src={logo} alt="706 Masters Pool" height="64" style={{ objectFit: "contain", flexShrink: 0 }} />
        <div>
          <h1>How to Enter</h1>
          <p>Masters Tournament &mdash; April 9–12, 2026</p>
        </div>
      </div>

      {/* ── Payment ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "0.75rem" }}>
          Pay Your Entry Fee
        </h2>
        <p style={{ marginBottom: "1rem", lineHeight: "1.7" }}>
          Entry fee is <strong>$10</strong>. Send via Venmo or PayPal before drafting. Include your{" "}
          <strong>username</strong> in the payment note so we can confirm your entry.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <PaymentRow platform="Venmo"  handle="@windell_11"   color="#008CFF" icon="V" />
          <PaymentRow platform="PayPal" handle="@JamesWindell" color="#003087" icon="P" />
        </div>
      </div>

      {/* ── Team Rules ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "1rem" }}>
          Team Rules
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          <InfoRow icon="6" label="Golfers per team"  value="Exactly 6 golfers" highlight />
          <InfoRow icon="$" label="Salary cap"        value="$50,000 total"     highlight />
          <InfoRow icon="1" label="Entries per person" value="One team per account" />
          <InfoRow icon="🔒" label="Lock time"        value="Thu Apr 9 · 8:00 AM ET" />
        </div>
      </div>

      {/* ── FYI ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "1rem" }}>
          Good to Know
        </h2>

        <ul style={{ paddingLeft: "1.25rem", lineHeight: "2.1", margin: 0 }}>
          <li><strong>Lowest combined score wins</strong> — stroke-play pool, not fantasy points.</li>
          <li>Higher-rated golfers cost more cap space — <strong>budget wisely</strong>.</li>
          <li>
            Bonuses lower your score: <strong>−1</strong> for best round of the day,{" "}
            <strong>−1</strong> per round your golfer leads solo, <strong>−5</strong> if your golfer wins.
          </li>
          <li>
            Missed-cut or withdrawn golfers take a <strong>+5 shot penalty</strong> — risky picks can hurt.
          </li>
          <li>Scores refresh automatically throughout each round during tournament days.</li>
          <li>
            See the full scoring breakdown on the{" "}
            {user
              ? <Link to="/rules" style={{ color: "var(--green-600)", fontWeight: 600 }}>Rules page</Link>
              : <strong>Rules page</strong>
            }.
          </li>
        </ul>
      </div>

      {/* ── CTA — only shown when not logged in ── */}
      {!user && (
        <>
          <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
            <Link to="/register" className="btn btn-primary" style={{ flex: 1, textAlign: "center" }}>
              Create Account
            </Link>
            <Link to="/login" className="btn btn-secondary" style={{ flex: 1, textAlign: "center" }}>
              Sign In
            </Link>
          </div>
          <p style={{ textAlign: "center", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "2rem" }}>
            Questions? Reach out to <strong>@windell_11</strong> on Venmo.
          </p>
        </>
      )}
    </div>
  );
}

function PaymentRow({ platform, handle, color, icon }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "0.875rem",
      padding: "0.875rem 1rem",
      background: "var(--green-50)",
      borderRadius: "var(--radius-md)",
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{
        width: "36px",
        height: "36px",
        borderRadius: "50%",
        background: color,
        color: "#fff",
        fontWeight: 700,
        fontSize: "1rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "1px" }}>{platform}</div>
        <div style={{ fontWeight: 700, fontSize: "1.05rem", color: "var(--green-800)" }}>{handle}</div>
      </div>
    </div>
  );
}

function InfoRow({ icon, label, value, highlight }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "0.75rem",
      padding: "0.625rem 0.875rem",
      background: highlight ? "var(--gold-50, #fdf8ec)" : "var(--green-50)",
      borderRadius: "var(--radius-md)",
    }}>
      <div style={{
        width: "28px",
        height: "28px",
        borderRadius: "var(--radius-sm)",
        background: highlight ? "var(--gold-400, #d4a017)" : "var(--green-200)",
        color: highlight ? "#3d2800" : "var(--green-700)",
        fontWeight: 700,
        fontSize: "0.85rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, fontSize: "0.875rem", color: "var(--text-muted)" }}>{label}</div>
      <div style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--green-800)" }}>{value}</div>
    </div>
  );
}
