// Mirrors the UserCreate validators in app/schemas/auth.py so the register
// form can flag bad input before submitting. The backend stays authoritative;
// keep the rules and messages here in sync with it.
//
// Each validator returns { value, error }: `value` is the normalized input to
// write back into the field, `error` is a message or null.

// Clash Royale tags only ever use these characters (no O, so a typed O is really a 0).
const CR_TAG_CHARS = "0289PYLQGRJCUV";
const CR_TAG_RE = new RegExp(`^#[${CR_TAG_CHARS}]{3,12}$`);
const FRIEND_LINK_RE =
  /(?:https?:\/\/)?link\.clashroyale\.com\/\?supercell_id&p=(\d+-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
const USERNAME_RE = /^[A-Za-z0-9_]{3,20}$/;
const PHONE_RE = /^\+\d{8,15}$/;

export function validateUsername(input) {
  const value = input.trim();
  return {
    value,
    error: USERNAME_RE.test(value)
      ? null
      : "Username must be 3-20 letters, digits, or underscores",
  };
}

export function validatePassword(input) {
  return {
    value: input,
    error: input.length >= 8 ? null : "Password must be at least 8 characters",
  };
}

export function validateCrTag(input) {
  let value = input.trim().toUpperCase().replaceAll("O", "0");
  if (!value.startsWith("#")) value = "#" + value;
  return {
    value,
    error: CR_TAG_RE.test(value)
      ? null
      : `Player tag must be # followed by 3-12 of these characters: ${CR_TAG_CHARS}`,
  };
}

export function validateFriendLink(input) {
  const match = input.match(FRIEND_LINK_RE);
  if (!match) {
    return {
      value: input.trim(),
      error: "Friend link must look like https://link.clashroyale.com/?supercell_id&p=...",
    };
  }
  return {
    value: `https://link.clashroyale.com/?supercell_id&p=${match[1].toLowerCase()}`,
    error: null,
  };
}

// Phone is optional unless SMS consent is checked; an empty value is valid here
// and the consent requirement is checked separately.
export function validatePhone(input) {
  if (!input.trim()) return { value: "", error: null };
  let value = input.replace(/[\s\-().]/g, "");
  if (/^\d{10}$/.test(value)) value = "+1" + value;
  return {
    value,
    error: PHONE_RE.test(value)
      ? null
      : "Phone number must be in international format, e.g. +15551234567",
  };
}
