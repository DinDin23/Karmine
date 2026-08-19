import { useEffect, useState } from "react";
import { getWagers } from "./api";
import { formatRelativeTime } from "./format";

const OUTCOME_LABEL = {
  win: "WIN",
  loss: "LOSS",
  refunded: "REFUNDED",
  pending: "LIVE",
};

function outcomeFor(wager, userId) {
  if (wager.status === "settled") return wager.winner_id === userId ? "win" : "loss";
  if (wager.status === "cancelled") return "refunded";
  return "pending";
}

export default function WagerHistory({ userId, refreshKey }) {
  const [wagers, setWagers] = useState([]);

  useEffect(() => {
    getWagers().then(setWagers);
  }, [refreshKey]);

  return (
    <div className="card">
      <h2>Wager History</h2>
      {wagers.length === 0 ? (
        <p className="empty-state">No wagers yet — queue up to get matched.</p>
      ) : (
        <ul className="list">
          {wagers.map((w) => {
            const opponent = w.player1_id === userId ? w.player2_username : w.player1_username;
            const outcome = outcomeFor(w, userId);
            return (
              <li key={w.id} className="wager-row">
                <span className={`outcome-badge outcome-${outcome}`}>
                  {OUTCOME_LABEL[outcome]}
                </span>
                <span className="wager-main">
                  vs {opponent} — ${w.stake_amount}
                </span>
                <span className="wager-time">{formatRelativeTime(w.created_at)}</span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
