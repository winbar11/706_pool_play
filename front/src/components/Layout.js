import { Outlet, NavLink, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../hooks/useTheme.js";
import logo from "../static/usa706.webp";
import logoOpenChampionship from "../static/usa706-open-championship.png";

export default function Layout() {
  const { user, logout } = useAuth();
  const theme = useTheme();
  const logoSrc = theme === "open-championship" ? logoOpenChampionship : logo;

  return (
    <div className="layout">
      <nav className="navbar">
        <Link to="/" className="navbar-brand">
          <img src={logoSrc} alt="706 Pool Play" height="46" style={{ objectFit: "contain" }} />
        </Link>

        <div className="navbar-nav">
          <NavLink to="/" end className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            Home
          </NavLink>
          <NavLink to="/leaderboard" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            Leaderboard
          </NavLink>
          <NavLink to="/draft" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            Draft
          </NavLink>
          <NavLink to="/my-team" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            My Team
          </NavLink>
          <NavLink to="/rules" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            Rules
          </NavLink>
          {user?.is_admin && (
            <NavLink to="/admin" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
              Admin
            </NavLink>
          )}
        </div>

        <div className="navbar-user">
          <span className="navbar-username">@{user?.username}</span>
          <button className="btn btn-ghost btn-sm" onClick={logout}>
            Sign out
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>

      <footer className="site-footer">
        <img src={logoSrc} alt="706 Pool Play" height="32" style={{ objectFit: "contain", opacity: 0.6 }} />
        <span className="footer-text">706 Pool Play</span>
      </footer>
    </div>
  );
}