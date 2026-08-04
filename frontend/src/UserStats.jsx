import { useEffect, useState } from "react";
import { getWagers } from "./api";

export default function UserStats({ userId, refreshKey }) {
  const [wagers, setWagers] = useState([]);

  useEffect(() => {
    getWagers().then(setWagers);
  }, [refreshKey]);

  const settled = wagers.filter((w) => w.status === "settled");
  const wins = settled.filter((w) => w.winner_id === userId).length;
  const losses = settled.length - wins;
  const winRate = settled.length ? Math.round((wins / settled.length) * 100) : 0;
  const netPnl = settled.reduce((total, w) => {
    const stake = Number(w.stake_amount);
    return total + (w.winner_id === userId ? stake : -stake);
  }, 0);

  return (
    <div className="card">
      <h2>Stats</h2>
      <div className="row">
        <span>Record: {wins}W – {losses}L</span>
        <span>({winRate}%)</span>
      </div>
      <p className={netPnl >= 0 ? "matched" : "error"}>
        Net P&L: {netPnl >= 0 ? "+" : ""}
        {netPnl.toFixed(2)}
      </p>
    </div>
  );
}
