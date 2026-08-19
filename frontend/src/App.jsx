import { useEffect, useState } from "react";
import AuthForm from "./AuthForm";
import Logo from "./Logo";
import UserStats from "./UserStats";
import Wallet from "./Wallet";
import Matchmaking from "./Matchmaking";
import WagerHistory from "./WagerHistory";
import { getMe, getToken, setToken } from "./api";
import "./App.css";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wagerRefreshKey, setWagerRefreshKey] = useState(0);
  const [balanceRefreshKey, setBalanceRefreshKey] = useState(0);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  function handleAuthenticated() {
    getMe().then(setUser);
  }

  function handleLogout() {
    setToken(null);
    setUser(null);
  }

  if (loading) return null;

  if (!user) {
    return (
      <div className="app landing">
        <div className="landing-hero">
          <p className="eyebrow">Clash Royale Wagering</p>
          <h1>
            <Logo className="logo-mark" /> Karmine
          </h1>
          <p className="tagline">Wager on your Clash Royale 1v1s. Queue up, get matched, get paid.</p>
        </div>
        <AuthForm onAuthenticated={handleAuthenticated} />
        <footer className="landing-footer">
          <a href="/privacy.html">Privacy Policy</a>
          <span aria-hidden="true">·</span>
          <a href="/terms.html">Terms of Service</a>
        </footer>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>
          <Logo className="logo-mark" /> Karmine
        </h1>
        <div className="user-badge">
          <span className="avatar">{user.username.slice(0, 1).toUpperCase()}</span>
          <span>{user.username}</span>
          <button onClick={handleLogout}>Log out</button>
        </div>
      </header>
      <div className="layout">
        <div className="column">
          <UserStats userId={user.id} refreshKey={wagerRefreshKey} />
          <Wallet onBalanceChanged={() => setBalanceRefreshKey((k) => k + 1)} />
          <WagerHistory userId={user.id} refreshKey={wagerRefreshKey} />
        </div>
        <div className="column">
          <Matchmaking
            userId={user.id}
            balanceRefreshKey={balanceRefreshKey}
            onWagerUpdated={() => {
              setWagerRefreshKey((k) => k + 1);
              setBalanceRefreshKey((k) => k + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
