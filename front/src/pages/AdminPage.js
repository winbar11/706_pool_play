import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api.js";

export default function AdminPage() {
  const qc = useQueryClient();
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [selectedTeamIds, setSelectedTeamIds] = useState([]);
  const [manualForm, setManualForm] = useState({
    golfer_id: "", round_num: "1", birdies: "0", eagles: "0", bogeys: "0",
    doubles: "0", worse: "0", pars: "0", ace: "0", double_eagle: "0",
    bogey_free: "0", birdie_streak: "0", round_score: ""
  });

  const { data: lbData } = useQuery({ queryKey: ["leaderboard"], queryFn: api.leaderboard.get });
  const { data: usersData } = useQuery({ queryKey: ["admin-users"], queryFn: api.admin.users });
  const { data: gData } = useQuery({ queryKey: ["golfers"], queryFn: api.golfers.list });

  const isLocked = lbData?.settings?.teams_locked === "1";
  const currentRound = lbData?.settings?.current_round || "0";
  const isTournamentComplete = lbData?.settings?.tournament_complete === "1";

  const notify = (m) => { setMsg(m); setErr(""); setTimeout(() => setMsg(""), 4000); };
  const fail = (e) => { setErr(e); setMsg(""); };

  const lockMut = useMutation({
    mutationFn: api.admin.lockTeams,
    onSuccess: () => { qc.invalidateQueries(["leaderboard"]); notify("Teams locked."); },
    onError: (e) => fail(e.message),
  });
  const unlockMut = useMutation({
    mutationFn: api.admin.unlockTeams,
    onSuccess: () => { qc.invalidateQueries(["leaderboard"]); notify("Teams unlocked."); },
    onError: (e) => fail(e.message),
  });
  const refreshMut = useMutation({
    mutationFn: api.admin.refresh,
    onSuccess: () => notify("Score refresh triggered — running in background."),
    onError: (e) => fail(e.message),
  });
  const roundMut = useMutation({
    mutationFn: (n) => api.admin.setRound(n),
    onSuccess: (_, n) => { qc.invalidateQueries(["leaderboard"]); notify(`Round set to ${n}.`); },
    onError: (e) => fail(e.message),
  });
  const tournamentCompleteMut = useMutation({
    mutationFn: (complete) => api.admin.setTournamentComplete(complete),
    onSuccess: (_, complete) => {
      qc.invalidateQueries(["leaderboard"]);
      notify(complete ? "Tournament marked complete. Winner bonus applied." : "Tournament marked in-progress. Winner bonus removed.");
    },
    onError: (e) => fail(e.message),
  });
  const clearTeamsMut = useMutation({
    mutationFn: api.admin.clearTeams,
    onSuccess: () => { qc.invalidateQueries(["leaderboard"]); notify("All teams cleared."); },
    onError: (e) => fail(e.message),
  });
  const deleteTeamsMut = useMutation({
    mutationFn: (ids) => api.admin.deleteTeams(ids),
    onSuccess: (_, ids) => {
      qc.invalidateQueries(["leaderboard"]);
      setSelectedTeamIds([]);
      notify(`${ids.length} team(s) deleted.`);
    },
    onError: (e) => fail(e.message),
  });
  const clearScoresMut = useMutation({
    mutationFn: api.admin.clearScores,
    onSuccess: () => {
      qc.invalidateQueries(["leaderboard"]);
      qc.invalidateQueries(["golfers"]);
      notify("All scores cleared.");
    },
    onError: (e) => fail(e.message),
  });
  const manualMut = useMutation({
    mutationFn: () => api.admin.updateGolfer({
      ...Object.fromEntries(
        Object.entries(manualForm).map(([k, v]) =>
          [k, k === "round_score" && v === "" ? null : Number(v) || 0]
        )
      ),
      golfer_id: parseInt(manualForm.golfer_id),
    }),
    onSuccess: () => {
      qc.invalidateQueries(["leaderboard"]);
      qc.invalidateQueries(["golfers"]);
      notify("Golfer updated successfully.");
    },
    onError: (e) => fail(e.message),
  });

  const mf = (e) => setManualForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const golfers = gData?.golfers || [];
  const users   = usersData?.users || [];
  const teams   = lbData?.teams || [];

  return (
    <div>
      <div className="page-header">
        <h1>Admin Panel</h1>
        <p>Manage the tournament, scores, and participants</p>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">{err}</div>}

      <div className="admin-grid">

        {/* Tournament controls */}
        <div className="card admin-section">
          <h3>Tournament Controls</h3>
          <div className="admin-btn-group">
            {isLocked ? (
              <button className="btn btn-secondary" onClick={() => unlockMut.mutate()}
                disabled={unlockMut.isPending}>
                🔓 Unlock Teams
              </button>
            ) : (
              <button className="btn btn-primary" onClick={() => lockMut.mutate()}
                disabled={lockMut.isPending}>
                🔒 Lock Teams (start tournament)
              </button>
            )}

            <button className="btn btn-secondary" onClick={() => refreshMut.mutate()}
              disabled={refreshMut.isPending}>
              {refreshMut.isPending ? "Refreshing…" : "⟳ Trigger Score Refresh Now"}
            </button>

            {isTournamentComplete ? (
              <button className="btn btn-secondary"
                onClick={() => tournamentCompleteMut.mutate(false)}
                disabled={tournamentCompleteMut.isPending}>
                ⏸ Mark In-Progress (remove winner bonus)
              </button>
            ) : (
              <button className="btn btn-primary"
                onClick={() => tournamentCompleteMut.mutate(true)}
                disabled={tournamentCompleteMut.isPending}>
                Tourney Complete (Winner Bonus)
              </button>
            )}

            <button
              className="btn btn-danger"
              onClick={() => {
                if (window.confirm("Clear ALL golfer scores and team points? This cannot be undone.")) {
                  clearScoresMut.mutate();
                }
              }}
              disabled={clearScoresMut.isPending}
            >
              {clearScoresMut.isPending ? "Clearing…" : "🧹 Clear All Scores"}
            </button>

            <button
              className="btn btn-danger"
              onClick={() => {
                if (window.confirm("Delete ALL teams? Players will need to re-draft. This cannot be undone.")) {
                  clearTeamsMut.mutate();
                }
              }}
              disabled={clearTeamsMut.isPending}
            >
              {clearTeamsMut.isPending ? "Clearing…" : "🗑️ Clear All Teams"}
            </button>
          </div>

          <hr className="divider" />
          <h3>Set Current Round</h3>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {[0, 1, 2, 3, 4].map(n => (
              <button
                key={n}
                className={`btn btn-sm ${parseInt(currentRound) === n ? "btn-primary" : "btn-ghost"}`}
                onClick={() => roundMut.mutate(n)}
              >
                {n === 0 ? "Pre-tournament" : `Round ${n}`}
              </button>
            ))}
          </div>
        </div>

        {/* Participants */}
        <div className="card admin-section">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <h3 style={{ margin: 0 }}>Participants ({users.length})</h3>
            {selectedTeamIds.length > 0 && (
              <button
                className="btn btn-danger btn-sm"
                disabled={deleteTeamsMut.isPending}
                onClick={() => {
                  const names = selectedTeamIds
                    .map(id => teams.find(t => t.id === id)?.team_name)
                    .filter(Boolean)
                    .join(", ");
                  if (window.confirm(`Delete ${selectedTeamIds.length} team(s)?\n${names}\n\nThis cannot be undone.`)) {
                    deleteTeamsMut.mutate(selectedTeamIds);
                  }
                }}
              >
                {deleteTeamsMut.isPending ? "Deleting…" : `Delete Selected (${selectedTeamIds.length})`}
              </button>
            )}
          </div>
          <table className="users-table">
            <thead>
              <tr>
                <th style={{ width: "2rem" }}></th>
                <th>Username</th>
                <th>Team</th>
                <th>Phone</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => {
                const team = teams.find(t => t.username === u.username);
                const checked = team ? selectedTeamIds.includes(team.id) : false;
                return (
                  <tr key={u.id} style={{ opacity: team ? 1 : 0.5 }}>
                    <td>
                      {team && (
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() =>
                            setSelectedTeamIds(prev =>
                              checked ? prev.filter(id => id !== team.id) : [...prev, team.id]
                            )
                          }
                        />
                      )}
                    </td>
                    <td>@{u.username}</td>
                    <td style={{ color: team ? "var(--text-primary)" : "var(--gray-500)" }}>
                      {team ? team.team_name : "—"}
                    </td>
                    <td style={{ color: u.phone ? "var(--text-primary)" : "var(--gray-500)", fontSize: "0.85rem" }}>
                      {u.phone || "—"}
                    </td>
                    <td>
                      {u.is_admin
                        ? <span className="badge badge-gold">Admin</span>
                        : <span className="badge badge-green">Player</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Manual score entry */}
        <div className="card admin-section" style={{ gridColumn: "1 / -1" }}>
          <h3>Manual Score Entry (ESPN API fallback)</h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
            Use this if the ESPN API is unavailable. Enter hole stats for a golfer's round and DK points will be recalculated automatically.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: "0.75rem" }}>
            <div className="form-group">
              <label>Golfer</label>
              <select name="golfer_id" value={manualForm.golfer_id} onChange={mf}>
                <option value="">Select golfer…</option>
                {golfers.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Round</label>
              <select name="round_num" value={manualForm.round_num} onChange={mf}>
                {[1,2,3,4].map(n => <option key={n} value={n}>Round {n}</option>)}
              </select>
            </div>
            {["birdies","eagles","bogeys","doubles","worse","pars","ace","double_eagle","bogey_free","birdie_streak","round_score"].map(field => (
              <div className="form-group" key={field}>
                <label>{field.replace(/_/g," ")}</label>
                <input name={field} type="number" value={manualForm[field]} onChange={mf} min="0" />
              </div>
            ))}
          </div>

          <button
            className="btn btn-primary mt-2"
            onClick={() => manualMut.mutate()}
            disabled={manualMut.isPending || !manualForm.golfer_id}
          >
            {manualMut.isPending ? "Saving…" : "Save Score"}
          </button>
        </div>

      </div>
    </div>
  );
}