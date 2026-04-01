import { Outlet, NavLink, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../static/706_pool_logo.png";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <nav className="navbar">
        <Link to="/" className="navbar-brand">
          <img src={logo} alt="706 Masters Pool" height="46" style={{ objectFit: "contain" }} />
        </Link>

        <div className="navbar-nav">
          <NavLink to="/" end className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            Leaderboard
          </NavLink>
          <NavLink to="/draft" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            Draft
          </NavLink>
          <NavLink to="/my-team" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            My Team
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
    </div>
  );
}