import { LogoMark } from "./LogoMark.jsx";

function fmtYear(iso) {
  return typeof iso === "string" && iso.length >= 4 ? iso.slice(0, 4) : null;
}

/**
 * Public entry screen (signed out). Minimal, factual, meta-driven — the three
 * capabilities mirror the actual tabs, and every number comes from /api/meta.
 */
export default function Landing({ meta, onSignIn, onGuest }) {
  const war = meta?.war;
  const win = meta?.window;
  const warText = war
    ? `Safe ≥ ${war.safe} · Moderate ${war.moderate}–${war.safe} · High ${war.high}–${war.moderate} · Shortage < ${war.high}`
    : null;
  const years = win ? [fmtYear(win.min_date), fmtYear(win.max_date)] : [null, null];

  return (
    <div className="landing-page">
      <header className="land-head">
        <div className="brand">
          <LogoMark size={30} />
          <h1>WaterSphere AI</h1>
        </div>
        <span className="govtag">BMC · Water Operations</span>
      </header>

      <main className="land-hero">
        <p className="land-kicker">Municipal water-management platform</p>
        <h2>Plan the city’s water<br />before it runs short.</h2>
        <p className="land-sub">
          A ward-level operating view of municipal water: demand forecasts,
          reservoir-aware stress classification, and fair supply plans — with
          citizens able to report incidents directly.
        </p>
        <div className="land-cta">
          <button className="primary" onClick={onSignIn}>Officer / citizen sign-in</button>
          <button className="secondary" onClick={onGuest}>Report a water issue without sign-in</button>
        </div>

        <ul className="land-stats">
          <li>
            <b>{meta?.ward_count ?? "—"}</b>
            <span>{meta?.ward_count ? "wards covered" : "wards"}</span>
          </li>
          <li>
            <b>24 h–7 d</b>
            <span>forecast horizons</span>
          </li>
          <li>
            <b>{win ? `Calibrated ${years[0] ?? "…"}–${years[1] ?? "…"}` : "… calculating"}</b>
            <span>ward telemetry</span>
          </li>
          <li>
            <b>{meta?.model_version ?? "…"}</b>
            <span>{warText ? "water-availability ratio bands: " + warText : "model registry version"}</span>
          </li>
        </ul>
      </main>

      <section className="land-steps" aria-label="How it works">
        <article>
          <span className="land-step-n">01</span>
          <h3>Forecast</h3>
          <p>Per-ward demand estimates across 1 / 3 / 7-day horizons, validated against recorded consumption.</p>
        </article>
        <article>
          <span className="land-step-n">02</span>
          <h3>Stress</h3>
          <p>Every ward scored as a water-availability ratio and classified — Safe, Moderate, High Stress or Shortage.</p>
        </article>
        <article>
          <span className="land-step-n">03</span>
          <h3>Plan</h3>
          <p>Reservoir storage turned into a severity-weighted supply plan, with alerts where supply falls short.</p>
        </article>
      </section>

      <footer className="land-foot">
        <span>WaterSphere AI · pilot deployment</span>
        <button className="linklike" onClick={onSignIn}>Sign in to continue →</button>
      </footer>
    </div>
  );
}
