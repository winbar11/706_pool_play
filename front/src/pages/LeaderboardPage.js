import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../utils/api.js";
import { useAuth } from "../context/AuthContext.js";
import logo from "../static/706_pool_logo.svg";

function fmtScore(score) {
  if (score === null || score === undefined) return "—";
  if (score === 0) return "E";
  return score > 0 ? `+${score}` : `${score}`;
}

function fmtRound(golfers, roundKey) {
  const scores = golfers
    .map(g => g[roundKey])
    .filter(s => s !== null && s !== undefined && s >= 60);
  if (scores.length === 0) return "—";
  const total = scores.reduce((s, v) => s + v, 0);
  const toPar = total - (72 * scores.length);
  return fmtScore(toPar);
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
    refetchInterval: 5 * 60 * 1000,
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
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <img src={logo} alt="706 Masters Pool" height="52" style={{ objectFit: "contain" }} />
          <div>
            <div className="banner-title">706 Masters Pool</div>
            <div className="banner-sub">
              Valero Texas Open · TPC San Antonio · Apr 3–6, 2026
              {isLocked && (
                <span className="badge badge-gold" style={{ marginLeft: "0.75rem" }}>
                  TEAMS LOCKED
                </span>
              )}
            </div>
          </div>
        </div>
        <RoundPills current={currentRound} />
      </div>

      <div className="page-header">
        <h1>Pool Leaderboard</h1>
        <p>
          {teams.length} {teams.length === 1 ? "entry" : "entries"} · Lowest score wins · Updated end-of-round
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
                <th className="right" style={{ width: 60 }}>R1</th>
                <th className="right" style={{ width: 60 }}>R2</th>
                <th className="right" style={{ width: 60 }}>R3</th>
                <th className="right" style={{ width: 60 }}>R4</th>
                <th className="right" style={{ width: 70 }}>Bonus</th>
                <th className="right" style={{ width: 80 }}>Score</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team, idx) => {
                const isOpen     = expanded === team.id;
                const rankClass  = idx === 0 ? "rank-1" : idx === 1 ? "rank-2" : idx === 2 ? "rank-3" : "rank-other";
                const isMe       = team.username === user?.username;
                const finalScore = team.final_score ?? null;
                const bonusShots = team.bonus_shots || 0;

                return (
                  <>
                    <tr key={team.id} className="team-row" onClick={() => toggleExpand(team.id)}>
                      <td>
                        <span className={`rank-cell ${rankClass}`}>{idx + 1}</span>
                      </td>
                      <td className="team-name-cell">
                        <div className="team-name">
                          {team.team_name}
                          {isMe && (
                            <span className="badge badge-gold" style={{ marginLeft: "0.5rem" }}>You</span>
                          )}
                        </div>
                        <div className="owner">@{team.username}</div>
                      </td>
                      <td className="dk-points-small">{fmtRound(team.golfers, "round1_score")}</td>
                      <td className="dk-points-small">{fmtRound(team.golfers, "round2_score")}</td>
                      <td className="dk-points-small">{fmtRound(team.golfers, "round3_score")}</td>
                      <td className="dk-points-small">{fmtRound(team.golfers, "round4_score")}</td>
                      <td className="dk-points-small" style={{
                        color: bonusShots < 0 ? "var(--green-600)" : "var(--text-muted)",
                        fontWeight: bonusShots < 0 ? "600" : "400"
                      }}>
                        {bonusShots < 0 ? bonusShots : "—"}
                      </td>
                      <td className="dk-points" style={{
                        color: finalScore !== null && finalScore < 0
                          ? "var(--green-600)"
                          : finalScore !== null && finalScore > 0
                          ? "#b91c1c"
                          : "var(--text-muted)"
                      }}>
                        {fmtScore(finalScore)}
                      </td>
                    </tr>

                    {isOpen && (
                      <tr key={`${team.id}-golfers`} className="team-golfers-row">
                        <td colSpan={8}>
                          <div className="golfer-chips">
                            {team.golfers.map(g => {
                              const missed   = g.made_cut === 0;
                              const isLeader = !!(g.solo_leader_r1 || g.solo_leader_r2 ||
                                               g.solo_leader_r3 || g.solo_leader_r4);
                              const displayScore = missed && g.total_score !== null
                                ? g.total_score + 8
                                : g.total_score;

                              return (
                                <div key={g.id} className={`golfer-chip ${missed ? "chip-cut" : ""}`}>
                                  <div>
                                    <div className="chip-name">
                                      {g.name}
                                      {missed && <span className="cut-badge">CUT +8</span>}
                                      {isLeader && (
                                        <span className="badge badge-gold" style={{ marginLeft: "0.3rem", fontSize: "0.62rem" }}>
                                          ★ Leader
                                        </span>
                                      )}
                                    </div>
                                    <div className="chip-score">
                                      {displayScore !== null && displayScore !== undefined
                                        ? fmtScore(displayScore)
                                        : "—"}
                                      {g.finish_position > 0 && !missed &&
                                        ` · ${g.finish_position === 1 ? "🏆 Winner" : `T${g.finish_position}`}`
                                      }
                                    </div>
                                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px" }}>
                                      {[1, 2, 3, 4]
                                        .map(r => g[`round${r}_score`] !== null && g[`round${r}_score`] !== undefined
                                          ? `R${r}: ${g[`round${r}_score`]}`
                                          : null)
                                        .filter(Boolean)
                                        .join(" · ")}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                          {bonusShots < 0 && (
                            <div style={{
                              marginTop: "0.5rem",
                              fontSize: "0.78rem",
                              color: "var(--green-600)",
                              paddingLeft: "0.25rem"
                            }}>
                              ★ Bonus shots: {bonusShots}
                              {team.golfers.some(g =>
                                g.finish_position === 1 && g.made_cut === 1 && g.current_round >= 4
                              ) && " (includes −5 winner bonus)"}
                            </div>
                          )}
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
        Click any row to expand · Lowest score wins · Missed cut = score + 8 penalty ·
        Best unique round = −1 · Solo round leader = −1 · Pick the winner = −5
      </p>
    </div>
  );
}