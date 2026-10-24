// Kirish oynasi: server 401 qaytarsa (MEBELIX_AUTH_REQUIRED=1) — login/parol → JWT.
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { LogIn } from "lucide-react";
import { ApiError, login } from "../api/client";
import { Btn } from "../shared/ui";
import { Logo } from "./Logo";
import "./login.css";

export function Login({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setErr("");
    try {
      await login(user.trim(), pass);
      onDone();
    } catch (x) {
      setErr(x instanceof ApiError ? x.message : String(x));
      setBusy(false);
    }
  };

  return (
    <div className="login-back">
      <form className="login-card" onSubmit={(e) => void submit(e)} data-testid="login-form">
        <Logo />
        <h1 className="login-title">{t("login.title")}</h1>
        <label className="login-field">
          <span>{t("login.user")}</span>
          <input value={user} onChange={(e) => setUser(e.target.value)} autoFocus autoComplete="username"
            data-testid="login-user" />
        </label>
        <label className="login-field">
          <span>{t("login.pass")}</span>
          <input type="password" value={pass} onChange={(e) => setPass(e.target.value)} autoComplete="current-password"
            data-testid="login-pass" />
        </label>
        {err && <div className="login-err" role="alert">{err}</div>}
        <Btn type="submit" kind="primary" icon={LogIn} label={busy ? t("login.busy") : t("login.submit")}
          disabled={busy || !user.trim()} testid="login-submit" />
      </form>
    </div>
  );
}
