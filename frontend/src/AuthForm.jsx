import { useState } from "react";
import { login, register } from "./api";

export default function AuthForm({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [crPlayerTag, setCrPlayerTag] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [supercellIdLink, setSupercellIdLink] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "register") {
        await register({
          username,
          email,
          password,
          cr_player_tag: crPlayerTag,
          phone_number: phoneNumber,
          supercell_id_link: supercellIdLink,
        });
      }
      await login({ email, password });
      onAuthenticated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h2>{mode === "login" ? "Log in" : "Register"}</h2>
      <form onSubmit={handleSubmit}>
        {mode === "register" && (
          <>
            <label>
              Username
              <input value={username} onChange={(e) => setUsername(e.target.value)} required />
            </label>
            <label>
              CR Player Tag
              <input
                value={crPlayerTag}
                onChange={(e) => setCrPlayerTag(e.target.value)}
                placeholder="#ABC123XY"
                required
              />
            </label>
            <label>
              Phone Number
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+15551234567"
                required
              />
            </label>
            <p className="sms-consent">
              By providing your phone number, you agree to receive SMS text
              messages from Karmine, including your opponent's Clash Royale
              friend link after a match. Message frequency varies. Message
              and data rates may apply. Reply STOP to opt out at any time, or
              HELP for help.
            </p>
            <label>
              Supercell ID Friend Link
              <input
                value={supercellIdLink}
                onChange={(e) => setSupercellIdLink(e.target.value)}
                placeholder="https://link.clashroyale.com/?supercell_id&p=..."
                required
              />
            </label>
          </>
        )}
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          {mode === "login" ? "Log in" : "Register"}
        </button>
      </form>
      <button
        className="link-button"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
      >
        {mode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
      </button>
    </div>
  );
}
