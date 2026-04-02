import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../utils/api.js";
import { useAuth } from "../context/AuthContext.js";

function fmtScore(s) {
  if (s === null || s === undefined) return "—";
  if (s === 0) return "E";
  return s > 0 ? `+${s}` : `${s}`;
}

function fmtRoundScore(s) {
  if (s === null || s === undefined) return "—";
  return s;
}

export default function MyTeamPage() {
  const { user } = useAuth();

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

  const teams = lbData?.teams || [];
  const myRank = teams.findIndex(t => t.id === team?.id) + 1;

  if (!team) {
    return (
      <div>
        <div className="page-header"><h1>My Team</h1></div>
        <div className="card empty-state">
          <div className="empty-icon">📋</div>
          <h3>No team submitted yet</h3>
          <p>Head to the draft page to build your lineup.</p>
          <Link to="/draft" className="btn btn-primary mt-2">Go to Draft →</Link>
        </div>
      </div>
    );
  }

  const golfers  = team.golfers || [];
  const myTeamLb = teams.find(t => t.id === team.id);
  const finalScore  = myTeamLb?.final_score ?? 0;
  const bonusShots  = myTeamLb?.bonus_shots ?? 0;
  const rawScore    = finalScore - bonusShots;

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
          <div className="stat-value" style={{ color: finalScore <= 0 ? "var(--green-600)" : "#b91c1c" }}>
            {fmtScore(finalScore)}
          </div>
          <div className="stat-label">Final Score</div>
        </div>
        {myRank > 0 && (
          <div className="stat-card">
            <div className="stat-value">#{myRank}</div>
            <div className="stat-label">Pool Rank</div>
          </div>
        )}
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--green-600)" }}>
            {bonusShots < 0 ? bonusShots : "—"}
          </div>
          <div className="stat-label">Bonus Shots</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{fmtScore(rawScore)}</div>
          <div className="stat-label">Raw Score</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{golfers.filter(g => g.made_cut !== 0).length}/6</div>
          <div className="stat-label">Made Cut</div>
        </div>
      </div>

      {!isLocked && (
        <Link to="/draft" className="btn btn-secondary"
          style={{ marginBottom: "1.5rem", display: "inline-flex" }}>
          ✏️ Edit lineup
        </Link>
      )}

      <div className="card">
        <h3 style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)", marginBottom: "0" }}>
          Golfer Breakdown
        </h3>

        <div className="my-team-golfers">
          {golfers.map(g => {
            const missed    = g.made_cut === 0;
            const isLeader  = g.solo_leader_r1 || g.solo_leader_r2 ||
                              g.solo_leader_r3 || g.solo_leader_r4;
            const displayed = missed
              ? (g.total_score !== null ? g.total_score + 8 : "CUT")
              : g.total_score;

            return (
              <div key={g.id} className={`my-golfer-card ${missed ? "my-golfer-cut" : ""}`}>
                <div>
                  <div className="my-golfer-name">
                    {g.name}
                    {missed && <span className="cut-badge">MISSED CUT +8</span>}
                    {isLeader && (
                      <span className="badge badge-gold" style={{ marginLeft: "0.4rem" }}>
                        ★ Round Leader
                      </span>
                    )}
                    {g.finish_position === 1 && !missed && g.current_round >= 4 && (
                      <span className="badge badge-green" style={{ marginLeft: "0.4rem" }}>
                        🏆 Winner −5
                      </span>
                    )}
                  </div>
                  <div className="my-golfer-meta">
                    #{g.world_rank} · ${g.salary.toLocaleString()}
                    {g.finish_position && g.finish_position > 0 && !missed
                      ? ` · ${g.finish_position === 1 ? "Winner" : `T${g.finish_position}`}`
                      : ""}
                  </div>
                  <div className="round-pts">
                    {[1,2,3,4].map(r => {
                      const s = g[`round${r}_score`];
                      return s !== null && s !== undefined
                        ? <span key={r} className="rpt">R{r}: {s}</span>
                        : null;
                    })}
                  </div>
                </div>
                <div>
                  <div className="my-golfer-total"
                    style={{ color: displayed !== null && displayed <= 0 ? "var(--green-600)" : "#b91c1c" }}>
                    {fmtScore(displayed)}
                  </div>
                  <div className="my-golfer-salary">score</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card mt-2"
        style={{ fontSize: "0.82rem", color: "var(--text-muted)", lineHeight: "1.8" }}>
        <strong style={{ color: "var(--text-primary)" }}>Scoring rules</strong><br />
        Lowest cumulative score wins · Missed cut / WD = score + 8 penalty<br />
        Best unique round of day = −1 shot · Solo round leader = −1 shot · Pick the winner = −5 shots
      </div>
    </div>
  );
}