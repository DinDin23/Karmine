import { useEffect, useState } from "react";
import { getWagers } from "./api";

export default function WagerHistory({ refreshKey }) {
  const [wagers, setWagers] = useState([]);

  useEffect(() => {
    getWagers().then(setWagers);
  }, [refreshKey]);

  return (
    <div className="card">
      <h2>Wager History</h2>
      <ul className="list">
        {wagers.map((w) => (
          <li key={w.id}>
            #{w.id} — ${w.stake_amount} — {w.status}
            {w.winner_id ? ` — winner: #${w.winner_id}` : ""}
          </li>
        ))}
        {wagers.length === 0 && <li>No wagers yet</li>}
      </ul>
    </div>
  );
}
