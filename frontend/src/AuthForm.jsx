import { useState } from "react";
import { login, register } from "./api";

function initialMode() {
  if (typeof window === "undefined") return "login";
  return new URLSearchParams(window.location.search).get("mode") === "register"
    ? "register"
    : "login";
}

export default function AuthForm({ onAuthenticated }) {
  const [mode, setMode] = useState(initialMode);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [crPlayerTag, setCrPlayerTag] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [supercellIdLink, setSupercellIdLink] = useState("");
  const [smsConsent, setSmsConsent] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "register") {
        if (smsConsent && !phoneNumber.trim()) {
          setError(
            "Enter a phone number to receive SMS match notifications, or uncheck the box.",
          );
          setSubmitting(false);
          return;
        }
        await register({
          username,
          email,
          password,
          cr_player_tag: crPlayerTag,
          phone_number: smsConsent && phoneNumber.trim() ? phoneNumber.trim() : null,
          sms_consent: smsConsent,
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
            <div className="sms-optin">
              <p className="sms-optin-heading">
                SMS match notifications &mdash; optional, not required to register
              </p>
              <label className="sms-consent">
                <input
                  type="checkbox"
                  checked={smsConsent}
                  onChange={(e) => setSmsConsent(e.target.checked)}
                />
                <span>
                  <strong>Optional &mdash; not required to register.</strong> I
                  agree to receive SMS text messages from Karmine, including my
                  opponent's Clash Royale friend link after a match. Message
                  frequency varies. Message and data rates may apply. Reply STOP
                  to opt out at any time, or HELP for help. See our{" "}
                  <a href="/privacy.html" target="_blank" rel="noopener noreferrer">
                    Privacy Policy
                  </a>
                  ,{" "}
                  <a href="/terms.html" target="_blank" rel="noopener noreferrer">
                    Terms of Service
                  </a>
                  , and{" "}
                  <a
                    href="/sms-opt-in.html"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    SMS opt-in details
                  </a>
                  .
                </span>
              </label>
              <label>
                Phone Number (optional)
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="+15551234567"
                  required={smsConsent}
                />
              </label>
            </div>
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
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
              tabIndex={-1}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
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
