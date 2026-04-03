export default function RulesPage() {
  return (
    <div>
      <div className="page-header">
        <h1>Rules &amp; Scoring</h1>
        <p>How the 706 Pool scoring engine works</p>
      </div>

      {/* ── Overview ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "0.75rem" }}>
          The Basics
        </h2>
        <p style={{ marginBottom: "0.5rem" }}>
          Draft a team of <strong>6 golfers</strong> under or equal to the <strong>$50,000 salary cap</strong>.
          Your team's score is the combined score to par of all 6 golfers.
          <strong> Lowest total wins.</strong>
        </p>
        <p>
          Bonuses are earned throughout the tournament and subtracted from your raw score —
          so more bonuses means a lower (better) final score.
        </p>
      </div>

      {/* ── Score Formula ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "1rem" }}>
          Score Formula
        </h2>

        <div style={{
          background: "var(--green-900)",
          color: "var(--cream)",
          borderRadius: "var(--radius-md)",
          padding: "1.25rem 1.5rem",
          fontFamily: "monospace",
          fontSize: "0.95rem",
          lineHeight: "2",
          marginBottom: "1rem",
        }}>
          <div><span style={{ color: "var(--gold-400)" }}>Final Score</span> = Raw Score + Bonus Shots</div>
          <div style={{ paddingLeft: "1rem", color: "var(--green-200)" }}>
            Raw Score = sum of all 6 golfers' scores to par
          </div>
          <div style={{ paddingLeft: "2rem", color: "var(--green-200)", fontSize: "0.85rem" }}>
            (missed cut / WD / DQ golfers: their score + 8 penalty)
          </div>
          <div style={{ paddingLeft: "1rem", color: "var(--green-200)" }}>
            Bonus Shots = best-round + solo-leader + winner bonuses
          </div>
          <div style={{ paddingLeft: "2rem", color: "var(--green-200)", fontSize: "0.85rem" }}>
            (bonuses are negative — they lower your score)
          </div>
        </div>

        <p style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
          Example: Raw Score +12, Bonus Shots −3 → Final Score <strong>+9</strong>
        </p>
      </div>

      {/* ── Bonuses ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "1rem" }}>
          Bonuses
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <BonusRow
            label="Best Round of the Day"
            value="−1 shot"
            color="var(--green-600)"
            description={
              <>
                Awarded once per round to the team whose golfer posts the <strong>unique lowest
                single-round score</strong> across all golfers in the field. If two or more golfers
                tie for the best round, <strong>no bonus is awarded</strong> for that round.
              </>
            }
          />

          <BonusRow
            label="Solo Leader After a Round"
            value="−1 shot per round"
            color="var(--green-600)"
            description={
              <>
                If one of your golfers is the <strong>solo tournament leader</strong> after rounds
                1, 2, or 3, your team earns −1 shot for each such round. Ties do not count —
                must be an outright leader.
              </>
            }
          />

          <BonusRow
            label="Tournament Winner"
            value="−5 shots"
            color="var(--gold-500)"
            description={
              <>
                If one of your 6 golfers <strong>wins the tournament outright</strong> (finishes
                1st, made the cut, completed all 4 rounds), your team earns −5 shots. This is
                the single biggest bonus available.
              </>
            }
          />
        </div>
      </div>

      {/* ── Penalties ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "1rem" }}>
          Missed Cut &amp; Withdrawal Penalty
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <PenaltyRow
            label="Missed Cut / DQ"
            value="+8 shots"
            description="Golfer's 2-round score to par plus an 8-shot penalty is added to your raw score."
          />
          <PenaltyRow
            label="Late Withdrawal (never played)"
            value="+8 shots"
            description="If a golfer withdraws before playing any hole, a flat +8 penalty is applied."
          />
        </div>


      </div>

      {/* ── Salary Cap ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "0.75rem" }}>
          Salary Cap &amp; Draft Rules
        </h2>
        <ul style={{ paddingLeft: "1.25rem", lineHeight: "2" }}>
          <li>Pick exactly <strong>6 golfers</strong></li>
          <li>Total salary must be <strong>≤ $50,000</strong></li>
          <li>Higher-rated golfers cost more — budget wise</li>
          <li>Teams are <strong>locked when the tournament begins</strong> — no changes after lock</li>
          <li>One team per account</li>
        </ul>
      </div>

      {/* ── Tiebreaker ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "0.75rem" }}>
          Tiebreaker
        </h2>
        <p>
          In the event of a tie in final score, teams are ranked by <strong>fewest bonus shots
          used</strong> (i.e., the team that earned fewer bonuses but has the same final score
          had a lower raw score). If still tied, teams share the rank.
        </p>
      </div>

      {/* ── Quick Reference ── */}
      <div className="card">
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "1rem" }}>
          Quick Reference
        </h2>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid var(--green-100)" }}>
              <th style={{ textAlign: "left", padding: "0.5rem 0.75rem", color: "var(--text-secondary)" }}>Event</th>
              <th style={{ textAlign: "center", padding: "0.5rem 0.75rem", color: "var(--text-secondary)" }}>Score Adjustment</th>
              <th style={{ textAlign: "left", padding: "0.5rem 0.75rem", color: "var(--text-secondary)", minWidth: "160px" }}>Condition</th>
            </tr>
          </thead>
          <tbody>
            {[
              { event: "Golfer score (made cut)", adj: "Score to par", cond: "All 4 rounds played", positive: false },
              { event: "Missed cut / WD / DQ", adj: "+8 penalty", cond: "Added to their 2-round score", positive: true },
              { event: "Best round of day", adj: "−1 shot", cond: "Unique lowest round in field", positive: false },
              { event: "Solo leader after round", adj: "−1 shot", cond: "Per round (R1, R2, R3)", positive: false },
              { event: "Tournament winner", adj: "−5 shots", cond: "Golfer wins outright", positive: false },
            ].map(({ event, adj, cond, positive }) => (
              <tr key={event} style={{ borderBottom: "1px solid var(--cream-dark)" }}>
                <td style={{ padding: "0.6rem 0.75rem" }}>{event}</td>
                <td style={{
                  padding: "0.6rem 0.75rem",
                  textAlign: "center",
                  fontWeight: 600,
                  color: positive ? "#b91c1c" : "var(--green-600)",
                }}>{adj}</td>
                <td style={{ padding: "0.6rem 0.75rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>{cond}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function BonusRow({ label, value, color, description }) {
  return (
    <div style={{
      display: "flex",
      gap: "1rem",
      alignItems: "flex-start",
      padding: "0.875rem 1rem",
      background: "var(--green-50)",
      borderRadius: "var(--radius-md)",
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>{label}</div>
        <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: "1.5" }}>{description}</div>
      </div>
      <div style={{
        fontWeight: 700,
        fontSize: "1.1rem",
        color,
        whiteSpace: "nowrap",
        minWidth: "70px",
        textAlign: "right",
      }}>{value}</div>
    </div>
  );
}

function PenaltyRow({ label, value, description }) {
  return (
    <div style={{
      display: "flex",
      gap: "1rem",
      alignItems: "flex-start",
      padding: "0.875rem 1rem",
      background: "#fef2f2",
      borderRadius: "var(--radius-md)",
      borderLeft: "3px solid #b91c1c",
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>{label}</div>
        <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: "1.5" }}>{description}</div>
      </div>
      <div style={{
        fontWeight: 700,
        fontSize: "1.1rem",
        color: "#b91c1c",
        whiteSpace: "nowrap",
        minWidth: "70px",
        textAlign: "right",
      }}>{value}</div>
    </div>
  );
}
