"""Opaque browser sessions for the existing Safara username/password login."""

import hashlib
import re
import secrets


_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_token_hash(token: str) -> str | None:
    if not isinstance(token, str) or not _TOKEN_PATTERN.fullmatch(token):
        return None
    return hashlib.sha256(token.encode("ascii")).hexdigest()


# sessionStorage survives a refresh in the same tab and disappears when the tab
# is closed. Only this opaque token reaches the browser; passwords stay server-side.
# The component code is static and never interpolates user-provided HTML or JS.
SESSION_BRIDGE_JS = """
export default function(component) {
  const { data, setStateValue } = component;
  const key = "safara_session_v1";
  const valid = value => /^[A-Za-z0-9_-]{43}$/.test(value || "");
  try {
    if (data?.action === "clear") {
      sessionStorage.removeItem(key);
    } else if (data?.action === "set" && valid(data.token)) {
      sessionStorage.setItem(key, data.token);
    }
    let token = sessionStorage.getItem(key) || "";
    if (!valid(token)) {
      sessionStorage.removeItem(key);
      token = "";
    }
    setStateValue("session_token", token);
  } catch (_) {
    setStateValue("session_token", "");
  }
}
"""
