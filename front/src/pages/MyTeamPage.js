import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../utils/api";

function fmt(pts) {
  if (pts === null || pts === undefined) return "—";
  return pts.toFixed(1);
}

function fmtScore(s) {
  if (s === null || s === undefined) return null;
  if (s === 0) return "E";
  return s > 0 ? `+${s}` : `${s}`;
}

function RptBadge({ label, pts }) {
  if (!pts) return null;
  const cls = pts > 0 ? "positive" : pts < 0 ? "negative" : "";
  return <span className={`rpt ${cls}`}>{label}: {pts > 0 ? "+" : ""}{pts.toFixed(1)}</span>;
}

export default function MyTeamPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["my-team"],
    queryFn: api.teams.my,
  });

  const { data: lbData } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: api.leaderboard.get,
  });

  if (isLoading) return <div className="loading-screen"><span className="loader" /></div>;

  const team = data?.team;
  const isLocked = lbData?.settings?.teams_locked === "1";

  // Find my rank
  const teams = lbData?.teams || [];
  const myRank = teams.findIndex(t => t.id === team?.id) + 1;

  if (!team) {
    return (
      <div>
        <div className="page-header">
          <h1>My Team</h1>
        </div>
        <div className="card empty-state">
          <div className="empty-icon">📋</div>
          <h3>No team submitted yet</h3>
          <p>Head to the draft page to build your lineup.</p>
          <Link to="/draft" className="btn btn-primary mt-2">Go to Draft →</Link>
        </div>
      </div>
    );
  }

  const golfers = team.golfers || [];
  const totalPts = golfers.reduce((s, g) => s + (g.dk_total_points || 0), 0);

  return (
    <div>
      <div className="page-header">
        <h1>{team.team_name}</h1>
        <p>
          ${team.total_salary.toLocaleString()} / $50,000 salary cap
          {isLocked && <span className="badge badge-gold" style={{ marginLeft: "0.5rem" }}>🔒 Locked</span>}
        </p>
      </div>

      {/* Stats row */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{fmt(totalPts)}</div>
          <div className="stat-label">Total DK pts</div>
        </div>
        {myRank > 0 && (
          <div className="stat-card">
            <div className="stat-value">#{myRank}</div>
            <div className="stat-label">Pool rank</div>
          </div>
        )}
        <div className="stat-card">
          <div className="stat-value">{golfers.filter(g => g.made_cut !== 0).length}/6</div>
          <div className="stat-label">Made cut</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">${(50000 - team.total_salary).toLocaleString()}</div>
          <div className="stat-label">Cap remaining</div>
        </div>
      </div>

      {!isLocked && (
        <Link to="/draft" className="btn btn-secondary" style={{ marginBottom: "1.5rem", display: "inline-flex" }}>
          ✏️ Edit lineup
        </Link>
      )}

      <div className="card">
        <h3 style={{ fontFamily: "var(--font-display)", color: "var(--gold-300)", marginBottom: "0" }}>
          Golfer Breakdown
        </h3>

        <div className="my-team-golfers">
          {golfers.map(g => {
            const missed = g.made_cut === 0;
            return (
              <div key={g.id} className={`my-golfer-card ${missed ? "my-golfer-cut" : ""}`}>
                <div>
                  <div className="my-golfer-name">
                    {g.name}
                    {missed && <span className="cut-badge">MISSED CUT</span>}
                    {g.finish_position && !missed && (
                      <span className="badge badge-green" style={{ marginLeft: "0.4rem" }}>
                        T{g.finish_position}
                      </span>
                    )}
                  </div>
                  <div className="my-golfer-meta">
                    #{g.world_rank} · ${g.salary.toLocaleString()}
                    {g.total_score !== null && g.total_score !== undefined
                      ? ` · ${fmtScore(g.total_score)} overall`
                      : ""}
                  </div>
                  <div className="round-pts">
                    <RptBadge label="R1" pts={g.dk_r1_points} />
                    <RptBadge label="R2" pts={g.dk_r2_points} />
                    <RptBadge label="R3" pts={g.dk_r3_points} />
                    <RptBadge label="R4" pts={g.dk_r4_points} />
                  </div>
                </div>
                <div>
                  <div className="my-golfer-total">{fmt(g.dk_total_points)}</div>
                  <div className="my-golfer-salary">DK pts</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card mt-2" style={{ fontSize: "0.82rem", color: "var(--green-300)", lineHeight: "1.8" }}>
        <strong style={{ color: "var(--gold-200)" }}>DraftKings scoring reference</strong><br />
        Double Eagle +20 · Eagle +8 · Birdie +3 · Par +0.5 · Bogey −0.5 · Double Bogey −1<br />
        Bogey-free round +3 · 3+ birdie streak +3 · All 4 rounds under 70 +5 · Hole-in-one bonus +10<br />
        Finish: 1st +30 · 2nd +20 · 3rd +18 · 4th +16 · 5th +14 … 50th +1
      </div>
    </div>
  );
}