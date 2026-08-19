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

  // `settled` comes from getWagers() ordered newest-first, so the current
  // streak is just a run from the front; longest streak is order-independent.
  let currentStreak = 0;
  let currentStreakType = null;
  for (const w of settled) {
    const won = w.winner_id === userId;
    if (currentStreakType === null) {
      currentStreakType = won ? "W" : "L";
      currentStreak = 1;
    } else if ((won ? "W" : "L") === currentStreakType) {
      currentStreak += 1;
    } else {
      break;
    }
  }

  let longestWinStreak = 0;
  let run = 0;
  for (const w of settled) {
    if (w.winner_id === userId) {
      run += 1;
      longestWinStreak = Math.max(longestWinStreak, run);
    } else {
      run = 0;
    }
  }

  const biggestWin = settled
    .filter((w) => w.winner_id === userId)
    .reduce((max, w) => Math.max(max, Number(w.stake_amount) * 2), 0);

  const totalWagered = wagers.reduce((total, w) => total + Number(w.stake_amount), 0);
  const avgStake = wagers.length ? totalWagered / wagers.length : 0;

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
      {wagers.length > 0 && (
        <div className="stats-grid">
          {currentStreak > 0 && (
            <div className="stat-tile">
              <span className="stat-label">Current streak</span>
              <span className={`stat-value ${currentStreakType === "W" ? "matched" : "error"}`}>
                {currentStreak}{currentStreakType}
              </span>
            </div>
          )}
          {longestWinStreak > 0 && (
            <div className="stat-tile">
              <span className="stat-label">Best streak</span>
              <span className="stat-value matched">{longestWinStreak}W</span>
            </div>
          )}
          {biggestWin > 0 && (
            <div className="stat-tile">
              <span className="stat-label">Biggest win</span>
              <span className="stat-value matched">${biggestWin.toFixed(2)}</span>
            </div>
          )}
          <div className="stat-tile">
            <span className="stat-label">Total wagered</span>
            <span className="stat-value">${totalWagered.toFixed(2)}</span>
          </div>
          <div className="stat-tile">
            <span className="stat-label">Avg stake</span>
            <span className="stat-value">${avgStake.toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
