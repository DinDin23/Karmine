import { useEffect, useState } from "react";
import AuthForm from "./AuthForm";
import Wallet from "./Wallet";
import Matchmaking from "./Matchmaking";
import WagerHistory from "./WagerHistory";
import { getMe, getToken, setToken } from "./api";
import "./App.css";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wagerRefreshKey, setWagerRefreshKey] = useState(0);

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
      <div className="app">
        <h1>Karmine</h1>
        <AuthForm onAuthenticated={handleAuthenticated} />
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Karmine</h1>
        <div>
          <span>{user.username}</span>
          <button onClick={handleLogout}>Log out</button>
        </div>
      </header>
      <div className="grid">
        <Wallet />
        <Matchmaking onMatched={() => setWagerRefreshKey((k) => k + 1)} />
        <WagerHistory refreshKey={wagerRefreshKey} />
      </div>
    </div>
  );
}

export default App;
