import { useState } from "react";
import { login, register } from "./api";
import HelpSteps from "./HelpSteps";
import {
  validateCrTag,
  validateFriendLink,
  validatePassword,
  validatePhone,
  validateUsername,
} from "./validation";

const CR_TAG_HELP = [
  "Open Clash Royale and tap your name in the top-left corner to open your profile.",
  "Your player tag is shown under your name and starts with #.",
  "Tap the tag to copy it, then paste it here.",
];

const FRIEND_LINK_HELP = [
  "In Clash Royale, open Settings and tap Supercell ID.",
  "Go to Friends and tap Add friends.",
  "Share or copy your friend link and paste it here. Extra text around the link is fine; we'll pull the link out.",
];

const PHONE_REQUIRED = "A phone number is required to receive SMS match invites";

function FieldError({ id, message }) {
  if (!message) return null;
  return (
    <p id={id} className="field-error">
      {message}
    </p>
  );
}

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
  const [fieldErrors, setFieldErrors] = useState({});

  const isRegister = mode === "register";

  // Validate one register field when the user leaves it: write the normalized
  // value back so they see what we'll store, and show any error under it.
  function checkField(name, value, validate, setValue) {
    const result = validate(value);
    setValue(result.value);
    setFieldErrors((prev) => ({ ...prev, [name]: result.error }));
  }

  function errorProps(name) {
    return {
      "aria-invalid": fieldErrors[name] ? true : undefined,
      "aria-describedby": fieldErrors[name] ? `${name}-error` : undefined,
    };
  }

  function switchMode() {
    setMode(isRegister ? "login" : "register");
    setFieldErrors({});
    setError(null);
  }

  // Re-run every register check at submit time too: pressing Enter submits
  // without blurring the current field, and untouched fields never blurred.
  function validateRegisterForm() {
    const results = {
      username: validateUsername(username),
      password: validatePassword(password),
      crPlayerTag: validateCrTag(crPlayerTag),
      supercellIdLink: validateFriendLink(supercellIdLink),
      phoneNumber: smsConsent
        ? validatePhone(phoneNumber)
        : { value: phoneNumber, error: null },
    };
    if (smsConsent && !results.phoneNumber.error && !results.phoneNumber.value) {
      results.phoneNumber.error = PHONE_REQUIRED;
    }

    setUsername(results.username.value);
    setCrPlayerTag(results.crPlayerTag.value);
    setSupercellIdLink(results.supercellIdLink.value);
    setPhoneNumber(results.phoneNumber.value);
    setFieldErrors(
      Object.fromEntries(Object.entries(results).map(([name, r]) => [name, r.error])),
    );
    return Object.values(results).some((r) => r.error) ? null : results;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    let valid = null;
    if (isRegister) {
      valid = validateRegisterForm();
      if (!valid) {
        setError("Please fix the highlighted fields above.");
        return;
      }
    }
    setSubmitting(true);
    try {
      if (isRegister) {
        await register({
          username: valid.username.value,
          email,
          password,
          cr_player_tag: valid.crPlayerTag.value,
          phone_number: smsConsent ? valid.phoneNumber.value : null,
          sms_consent: smsConsent,
          supercell_id_link: valid.supercellIdLink.value,
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
      <h2>{isRegister ? "Register" : "Log in"}</h2>
      <form onSubmit={handleSubmit}>
        {isRegister && (
          <>
            <label>
              Username
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onBlur={(e) =>
                  e.target.value &&
                  checkField("username", e.target.value, validateUsername, setUsername)
                }
                autoComplete="username"
                required
                {...errorProps("username")}
              />
              <FieldError id="username-error" message={fieldErrors.username} />
            </label>
            <div className="field-with-help">
              <label>
                CR Player Tag
                <input
                  value={crPlayerTag}
                  onChange={(e) => setCrPlayerTag(e.target.value)}
                  onBlur={(e) =>
                    e.target.value &&
                    checkField("crPlayerTag", e.target.value, validateCrTag, setCrPlayerTag)
                  }
                  placeholder="#9Q9R2V0P"
                  autoCapitalize="characters"
                  autoCorrect="off"
                  spellCheck={false}
                  required
                  {...errorProps("crPlayerTag")}
                />
                <FieldError id="crPlayerTag-error" message={fieldErrors.crPlayerTag} />
              </label>
              <HelpSteps steps={CR_TAG_HELP} />
            </div>
            <div className="sms-optin">
              <p className="sms-optin-heading">SMS match notifications</p>
              <label className="sms-consent">
                <input
                  type="checkbox"
                  checked={smsConsent}
                  onChange={(e) => {
                    setSmsConsent(e.target.checked);
                    if (!e.target.checked) {
                      setFieldErrors((prev) => ({ ...prev, phoneNumber: null }));
                    }
                  }}
                />
                <span>
                  <strong>Optional &mdash; not required to register.</strong> I
                  agree to receive SMS text messages from Karmine, including my
                  opponent's Clash Royale friend link before the match. Message
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
                Phone Number
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  onBlur={(e) =>
                    smsConsent &&
                    checkField("phoneNumber", e.target.value, validatePhone, setPhoneNumber)
                  }
                  placeholder="+15551234567"
                  autoComplete="tel"
                  required={smsConsent}
                  {...errorProps("phoneNumber")}
                />
                <FieldError id="phoneNumber-error" message={fieldErrors.phoneNumber} />
              </label>
            </div>
            <div className="field-with-help">
              <label>
                Supercell ID Friend Link
                <input
                  value={supercellIdLink}
                  onChange={(e) => setSupercellIdLink(e.target.value)}
                  onBlur={(e) =>
                    e.target.value &&
                    checkField(
                      "supercellIdLink",
                      e.target.value,
                      validateFriendLink,
                      setSupercellIdLink,
                    )
                  }
                  placeholder="https://link.clashroyale.com/?supercell_id&p=..."
                  inputMode="url"
                  autoCapitalize="off"
                  autoCorrect="off"
                  spellCheck={false}
                  required
                  {...errorProps("supercellIdLink")}
                />
                <FieldError id="supercellIdLink-error" message={fieldErrors.supercellIdLink} />
              </label>
              <HelpSteps steps={FRIEND_LINK_HELP} />
            </div>
          </>
        )}
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label>
          Password
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={(e) =>
                isRegister &&
                e.target.value &&
                checkField("password", e.target.value, validatePassword, setPassword)
              }
              autoComplete={isRegister ? "new-password" : "current-password"}
              required
              {...(isRegister ? errorProps("password") : {})}
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
          {isRegister && <FieldError id="password-error" message={fieldErrors.password} />}
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          {isRegister ? "Register" : "Log in"}
        </button>
      </form>
      <button className="link-button" onClick={switchMode}>
        {isRegister ? "Already have an account? Log in" : "Need an account? Register"}
      </button>
    </div>
  );
}
