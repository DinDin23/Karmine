import { useEffect, useRef, useState } from "react";
import { cancelQueue, getMatchmakingStatus, matchmakingSocketUrl, queueMatch } from "./api";
import Tooltip from "./Tooltip";

const POLL_INTERVAL_MS = 20000;
const REVERT_DELAY_MS = 5000;

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function isTerminalWagerStatus(wagerStatus) {
  return wagerStatus === "settled" || wagerStatus === "cancelled";
}

function isInProgress(matchStatus, wagerStatus) {
  return matchStatus === "matched" && !isTerminalWagerStatus(wagerStatus);
}

export default function Matchmaking({ userId, onWagerUpdated }) {
  const [stake, setStake] = useState("10");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const socketRef = useRef(null);
  // Tracks the previously-seen {status, wagerStatus} so the transition effect
  // below can tell a *live* match/settle/expire event apart from just loading
  // an already-resolved request on mount (which should resume silently, with
  // no transient result panel or refresh callback).
  const prevRef = useRef({ status: null, wagerStatus: null });

  useEffect(() => {
    getMatchmakingStatus()
      .then((data) => {
        const wagerStatus = data?.wager_status ?? null;
        if (data?.status === "matched" && isTerminalWagerStatus(wagerStatus)) {
          // Already resolved before this widget ever saw it live -- resume at
          // the normal queue screen, not the transient result panel.
          prevRef.current = { status: null, wagerStatus: null };
          setStatus(null);
        } else {
          prevRef.current = { status: data?.status ?? null, wagerStatus };
          setStatus(data);
        }
      })
      .catch(() => setStatus(null));
  }, []);

  // Detects live transitions (via WS push or the polling fallback below) into
  // "just matched" or "just resolved" and reacts: bump the wager refresh
  // callback, and for a resolved match, show the result briefly before
  // reverting to the normal queue screen.
  useEffect(() => {
    const prev = prevRef.current;
    const wagerStatus = status?.wager_status ?? null;
    const becameMatched = status?.status === "matched" && prev.status !== "matched";
    const justResolved =
      status?.status === "matched" &&
      isTerminalWagerStatus(wagerStatus) &&
      !isTerminalWagerStatus(prev.wagerStatus);

    prevRef.current = { status: status?.status ?? null, wagerStatus };

    if (becameMatched || justResolved) onWagerUpdated?.();

    if (justResolved) {
      const timer = setTimeout(() => setStatus(null), REVERT_DELAY_MS);
      return () => clearTimeout(timer);
    }
  }, [status, onWagerUpdated]);

  useEffect(() => {
    if (status?.status !== "waiting") {
      setElapsed(0);
      return;
    }
    setElapsed(0);
    const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [status?.status]);

  // Stay connected through the whole "something might still change" lifecycle
  // (searching, and matched-but-not-yet-resolved) so settle/expire pushes
  // actually reach the widget -- not just while searching for an opponent.
  useEffect(() => {
    const shouldConnect =
      status?.status === "waiting" || isInProgress(status?.status, status?.wager_status);
    if (!shouldConnect) {
      socketRef.current?.close();
      return;
    }

    const socket = new WebSocket(matchmakingSocketUrl());
    socketRef.current = socket;
    socket.onmessage = (event) => setStatus(JSON.parse(event.data));

    return () => socket.close();
  }, [status?.status, status?.wager_status]);

  // Safety net alongside the WS push: if a message is ever missed (e.g. a
  // reconnect gap), pick up settle/expire on the next poll instead of hanging
  // in the matched panel forever.
  useEffect(() => {
    if (!isInProgress(status?.status, status?.wager_status)) return;
    const interval = setInterval(() => {
      getMatchmakingStatus()
        .then(setStatus)
        .catch(() => {});
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [status?.status, status?.wager_status]);

  async function handleQueue() {
    setError(null);
    try {
      const result = await queueMatch(Number(stake));
      setStatus(result);
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

  const wagerStatus = status?.wager_status ?? null;
  const resolved = status?.status === "matched" && isTerminalWagerStatus(wagerStatus);

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
      ) : resolved ? (
        <div>
          {wagerStatus === "settled" ? (
            <p className={status.winner_id === userId ? "matched" : "expired"}>
              {status.winner_id === userId
                ? `Match complete — you won $${(Number(status.stake_amount) * 2).toFixed(2)}!`
                : "Match complete — your opponent won this one."}
            </p>
          ) : (
            <p className="expired">
              Match cancelled — the game wasn't finished within 15 minutes. Your $
              {status.stake_amount} stake was refunded.
            </p>
          )}
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
              <Tooltip text="Open this link on your phone to launch Supercell ID. It sends your opponent a friend request in Clash Royale — once they accept, challenge them to a 1v1 friendly battle to play your match." />
            </p>
          )}
          <div className="searching">
            <span className="spinner" />
            <span>Waiting for your game to finish...</span>
          </div>
          <p className="elapsed">
            We'll detect the result automatically once your game is played — no need to report it.
          </p>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
