import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../utils/api";
import { useAuth } from "../context/AuthContext";

function fmt(pts) {
  if (pts === null || pts === undefined) return "—";
  return pts.toFixed(1);
}

function scoreDisplay(score) {
  if (score === null || score === undefined) return "—";
  if (score === 0) return "E";
  return score > 0 ? `+${score}` : `${score}`;
}

function RoundPills({ current }) {
  const rounds = ["R1", "R2", "R3", "R4"];
  const labels = ["Thu", "Fri", "Sat", "Sun"];
  const cur = parseInt(current) || 0;
  return (
    <div className="round-pills">
      {rounds.map((r, i) => {
        const num = i + 1;
        const cls = num < cur ? "complete" : num === cur ? "current" : "upcoming";
        return (
          <span key={r} className={`round-pill ${cls}`}>
            {r} · {labels[i]}
          </span>
        );
      })}
    </div>
  );
}

export default function LeaderboardPage() {
  const { user } = useAuth();
  const [expanded, setExpanded] = useState(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: api.leaderboard.get,
    refetchInterval: 5 * 60 * 1000, // refresh every 5 min
  });

  if (isLoading) return <div className="loading-screen"><span className="loader" /></div>;
  if (error) return <div className="alert alert-error">Failed to load leaderboard: {error.message}</div>;

  const { teams = [], settings = {} } = data;
  const currentRound = parseInt(settings.current_round) || 0;
  const isLocked = settings.teams_locked === "1";

  const toggleExpand = (id) => setExpanded(exp => exp === id ? null : id);

  return (
    <div>
      <div className="tournament-banner">
        <div>
          <div className="banner-title">The Masters Tournament</div>
          <div className="banner-sub">
            Masters 706 - Pool 2026
            {isLocked && <span className="badge badge-gold" style={{ marginLeft: "0.75rem" }}>🔒 Teams Locked</span>}
          </div>
        </div>
        <RoundPills current={currentRound} />
      </div>

      <div className="page-header">
        <h1>Pool Leaderboard</h1>
        <p>
          {teams.length} {teams.length === 1 ? "entry" : "entries"} · Scores updated end-of-round
        </p>
      </div>

      {teams.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon">🏌️</div>
          <h3>No teams yet</h3>
          <p>Be the first to submit your lineup!</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th style={{ width: 50 }}>Rank</th>
                <th>Team</th>
                <th className="right" style={{ width: 80 }}>R1</th>
                <th className="right" style={{ width: 80 }}>R2</th>
                <th className="right" style={{ width: 80 }}>R3</th>
                <th className="right" style={{ width: 80 }}>R4</th>
                <th className="right" style={{ width: 100 }}>DK Pts</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team, idx) => {
                const isOpen = expanded === team.id;
                const rankClass = idx === 0 ? "rank-1" : idx === 1 ? "rank-2" : idx === 2 ? "rank-3" : "rank-other";
                const isMe = team.username === user?.username;

                // Sum round points from golfers
                const r1 = team.golfers.reduce((s, g) => s + (g.dk_r1_points || 0), 0);
                const r2 = team.golfers.reduce((s, g) => s + (g.dk_r2_points || 0), 0);
                const r3 = team.golfers.reduce((s, g) => s + (g.dk_r3_points || 0), 0);
                const r4 = team.golfers.reduce((s, g) => s + (g.dk_r4_points || 0), 0);

                return (
                  <>
                    <tr key={team.id} className="team-row" onClick={() => toggleExpand(team.id)}>
                      <td>
                        <span className={`rank-cell ${rankClass}`}>
                          {idx + 1}
                        </span>
                      </td>
                      <td className="team-name-cell">
                        <div className="team-name">
                          {team.team_name}
                          {isMe && <span className="badge badge-gold" style={{ marginLeft: "0.5rem" }}>You</span>}
                        </div>
                        <div className="owner">@{team.username}</div>
                      </td>
                      <td className="dk-points-small">{r1 > 0 ? fmt(r1) : "—"}</td>
                      <td className="dk-points-small">{r2 > 0 ? fmt(r2) : "—"}</td>
                      <td className="dk-points-small">{r3 > 0 ? fmt(r3) : "—"}</td>
                      <td className="dk-points-small">{r4 > 0 ? fmt(r4) : "—"}</td>
                      <td className="dk-points">{fmt(team.dk_total_points)}</td>
                    </tr>
                    {isOpen && (
                      <tr key={`${team.id}-golfers`} className="team-golfers-row">
                        <td colSpan={7}>
                          <div className="golfer-chips">
                            {team.golfers.map(g => (
                              <div key={g.id} className={`golfer-chip ${!g.made_cut ? "chip-cut" : ""}`}>
                                <div>
                                  <div className="chip-name">
                                    {g.name}
                                    {!g.made_cut && <span className="cut-badge">CUT</span>}
                                  </div>
                                  <div className="chip-score">
                                    {g.total_score !== null ? scoreDisplay(g.total_score) : "—"}
                                    {g.finish_position ? ` · T${g.finish_position}` : ""}
                                  </div>
                                </div>
                                <div className="chip-pts">{fmt(g.dk_total_points)} pts</div>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-muted mt-2" style={{ fontSize: "0.78rem", textAlign: "center" }}>
        Click any row to expand golfer breakdown · DK scoring: Eagle +8, Birdie +3, Par +0.5, Bogey −0.5
      </p>
    </div>
  );
}