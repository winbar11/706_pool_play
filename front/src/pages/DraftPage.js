import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../utils/api";

const SALARY_CAP = 50000;
const ROSTER_SIZE = 6;

export default function DraftPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [selected, setSelected] = useState([]);   // array of golfer objects
  const [teamName, setTeamName] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const { data: gData, isLoading } = useQuery({
    queryKey: ["golfers"],
    queryFn: api.golfers.list,
  });

  const { data: lbData } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: api.leaderboard.get,
  });

  const { data: myTeamData } = useQuery({
    queryKey: ["my-team"],
    queryFn: api.teams.my,
    onSuccess: (d) => {
      if (d.team) {
        setTeamName(d.team.team_name);
        setSelected(d.team.golfers);
      }
    },
  });

  const isLocked = lbData?.settings?.teams_locked === "1";

  const mutation = useMutation({
    mutationFn: () => api.teams.submit(teamName, selected.map(g => g.id)),
    onSuccess: () => {
      qc.invalidateQueries(["my-team"]);
      qc.invalidateQueries(["leaderboard"]);
      setSuccess("Team saved! Head to the leaderboard to track your score.");
    },
    onError: (err) => setError(err.message),
  });

  const golfers = gData?.golfers || [];

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return golfers.filter(g =>
      !q || g.name.toLowerCase().includes(q) || (g.country || "").toLowerCase().includes(q)
    );
  }, [golfers, search]);

  const spent = selected.reduce((s, g) => s + g.salary, 0);
  const remaining = SALARY_CAP - spent;
  const pct = Math.min((spent / SALARY_CAP) * 100, 100);
  const capClass = pct > 100 ? "over" : pct > 90 ? "warn" : "safe";

  const toggle = (golfer) => {
    if (isLocked) return;
    const idx = selected.findIndex(g => g.id === golfer.id);
    if (idx >= 0) {
      setSelected(s => s.filter(g => g.id !== golfer.id));
    } else {
      if (selected.length >= ROSTER_SIZE) {
        setError(`You can only select ${ROSTER_SIZE} golfers`);
        setTimeout(() => setError(""), 2500);
        return;
      }
      if (spent + golfer.salary > SALARY_CAP) {
        setError("Adding this golfer would exceed the $50,000 salary cap");
        setTimeout(() => setError(""), 2500);
        return;
      }
      setSelected(s => [...s, golfer]);
    }
  };

  const remove = (golfer) => setSelected(s => s.filter(g => g.id !== golfer.id));

  const submit = () => {
    setError("");
    setSuccess("");
    if (!teamName.trim()) { setError("Please enter a team name"); return; }
    if (selected.length !== ROSTER_SIZE) {
      setError(`Select exactly ${ROSTER_SIZE} golfers`); return;
    }
    if (spent > SALARY_CAP) { setError("You are over the salary cap"); return; }
    mutation.mutate();
  };

  if (isLoading) return <div className="loading-screen"><span className="loader" /></div>;

  return (
    <div>
      <div className="page-header">
        <h1>Draft Your Team</h1>
        <p>Pick {ROSTER_SIZE} golfers · $50,000 salary cap · DraftKings scoring</p>
      </div>

      {isLocked && (
        <div className="locked-banner">
          🔒 The tournament has started — teams are locked and cannot be changed.
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="draft-layout">
        {/* Left: golfer list */}
        <div>
          <div className="card">
            <div className="golfer-search form-group" style={{ marginBottom: "1rem" }}>
              <input
                placeholder="Search golfers by name or country…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>

            <div className="flex-between" style={{ marginBottom: "0.75rem" }}>
              <span style={{ fontSize: "0.8rem", color: "var(--green-300)" }}>
                {filtered.length} golfers
              </span>
              <span style={{ fontSize: "0.8rem", color: "var(--green-300)" }}>
                {selected.length}/{ROSTER_SIZE} selected
              </span>
            </div>

            <div className="golfer-list">
              {filtered.map((g) => {
                const isSel = selected.some(s => s.id === g.id);
                const wouldExceed = !isSel && spent + g.salary > SALARY_CAP;
                const isFull = !isSel && selected.length >= ROSTER_SIZE;
                const isDisabled = isLocked || wouldExceed || isFull;

                return (
                  <div
                    key={g.id}
                    className={`golfer-row ${isSel ? "selected" : ""} ${isDisabled ? "disabled" : ""}`}
                    onClick={() => !isDisabled && toggle(g)}
                  >
                    <div className="golfer-row-left">
                      <span className="golfer-rank">#{g.world_rank}</span>
                      <div className="golfer-info">
                        <div className="golfer-name">{g.name}</div>
                        <div className="golfer-country">{g.country}</div>
                      </div>
                    </div>
                    <div className="golfer-row-right">
                      <span className="golfer-salary">${g.salary.toLocaleString()}</span>
                      {isSel && <span className="check-icon">✓</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right: roster */}
        <div className="roster-card card">
          <h3 style={{ fontFamily: "var(--font-display)", color: "var(--gold-300)", marginBottom: "1rem" }}>
            Your Roster
          </h3>

          {/* Salary cap bar */}
          <div>
            <div className="salary-cap-bar">
              <div className={`salary-cap-fill ${capClass}`} style={{ width: `${pct}%` }} />
            </div>
            <div className="cap-numbers">
              <span className={remaining < 0 ? "over-text spent" : "spent"}>
                ${spent.toLocaleString()} spent
              </span>
              <span className={remaining < 0 ? "over-text" : ""}>
                {remaining < 0
                  ? `$${Math.abs(remaining).toLocaleString()} over cap`
                  : `$${remaining.toLocaleString()} remaining`}
              </span>
            </div>
          </div>

          <hr className="divider" />

          {/* Slots */}
          <div className="roster-slots">
            {Array.from({ length: ROSTER_SIZE }).map((_, i) => {
              const g = selected[i];
              return (
                <div key={i} className={`roster-slot ${g ? "filled" : ""}`}>
                  {g ? (
                    <>
                      <div>
                        <div className="slot-player">{g.name}</div>
                        <div className="slot-salary">${g.salary.toLocaleString()}</div>
                      </div>
                      {!isLocked && (
                        <button className="slot-remove" onClick={() => remove(g)}>✕</button>
                      )}
                    </>
                  ) : (
                    <span className="slot-label">Golfer {i + 1}</span>
                  )}
                </div>
              );
            })}
          </div>

          <hr className="divider" />

          {/* Team name */}
          <div className="form-group team-name-input">
            <label>Team name</label>
            <input
              placeholder="e.g. Eagle Chasers"
              value={teamName}
              onChange={e => setTeamName(e.target.value)}
              disabled={isLocked}
            />
          </div>

          <button
            className="btn btn-primary btn-full"
            onClick={submit}
            disabled={isLocked || mutation.isPending || selected.length !== ROSTER_SIZE || spent > SALARY_CAP}
          >
            {mutation.isPending ? "Saving…" : myTeamData?.team ? "Update Team" : "Submit Team"}
          </button>

          {myTeamData?.team && (
            <button
              className="btn btn-ghost btn-full mt-1"
              onClick={() => navigate("/my-team")}
            >
              View my team →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}