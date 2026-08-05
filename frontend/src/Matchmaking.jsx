import { useEffect, useRef, useState } from "react";
import { cancelQueue, getMatchmakingStatus, matchmakingSocketUrl, queueMatch } from "./api";

export default function Matchmaking({ onMatched }) {
  const [stake, setStake] = useState("10");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    getMatchmakingStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

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
      <h2>Matchmaking</h2>
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
          <p>Waiting for an opponent at ${status.stake_amount}...</p>
          <button onClick={handleCancel}>Cancel</button>
        </div>
      ) : (
        <div>
          <p className="matched">
            Matched! Opponent #{status.opponent_id}, wager #{status.wager_id}, stake $
            {status.stake_amount}
          </p>
          <p>Check your texts for your opponent's Clash Royale friend link.</p>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
