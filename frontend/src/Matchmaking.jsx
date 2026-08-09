import { useEffect, useRef, useState } from "react";
import { cancelQueue, getMatchmakingStatus, matchmakingSocketUrl, queueMatch } from "./api";

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function Matchmaking({ onMatched }) {
  const [stake, setStake] = useState("10");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const socketRef = useRef(null);

  useEffect(() => {
    getMatchmakingStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    if (status?.status !== "waiting") {
      setElapsed(0);
      return;
    }
    setElapsed(0);
    const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [status?.status]);

  useEffect(() => {
    if (status?.status !== "waiting") {
      socketRef.current?.close();
      return;
    }

    const socket = new WebSocket(matchmakingSocketUrl());
    socketRef.current = socket;
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
      if (data.status === "matched") onMatched?.();
    };

    return () => socket.close();
  }, [status?.status, onMatched]);

  async function handleQueue() {
    setError(null);
    try {
      const result = await queueMatch(Number(stake));
      setStatus(result);
      if (result.status === "matched") onMatched?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCancel() {
    setError(null);
    try {
      await cancelQueue();
      setStatus(null);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h2>Clash Royale Matchmaking</h2>
      {!status || status.status === "cancelled" ? (
        <div className="row">
          <input
            type="number"
            min="0"
            step="0.01"
            value={stake}
            onChange={(e) => setStake(e.target.value)}
          />
          <button onClick={handleQueue}>Queue</button>
        </div>
      ) : status.status === "waiting" ? (
        <div>
          <div className="searching">
            <span className="spinner" />
            <span>
              Searching for an opponent at ${status.stake_amount}
              <span className="dots">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            </span>
          </div>
          <p className="elapsed">{formatElapsed(elapsed)} elapsed</p>
          <button onClick={handleCancel}>Cancel</button>
        </div>
      ) : (
        <div>
          <p className="matched">
            Matched! Opponent #{status.opponent_id}, wager #{status.wager_id}, stake $
            {status.stake_amount}
          </p>
          <p>Check your texts for your opponent's Clash Royale friend link.</p>
          {status.opponent_supercell_link && (
            <p>
              Or add them directly:{" "}
              <a href={status.opponent_supercell_link} target="_blank" rel="noreferrer">
                {status.opponent_supercell_link}
              </a>
            </p>
          )}
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
