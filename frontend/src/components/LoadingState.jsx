import React, { useState, useEffect } from "react";

const STEPS = [
  { id: "fetch",     label: "Fetching product pages…"      },
  { id: "extract",   label: "Extracting product data…"     },
  { id: "ai",        label: "Running AI analysis…"         },
  { id: "score",     label: "Scoring & ranking deals…"     },
];

export default function LoadingState() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-state">
      <div className="loading-orb">
        <div className="loading-orb-inner">
          <div className="loading-orb-core">🤖</div>
        </div>
      </div>

      <p style={{ fontWeight: 700, fontSize: 15, marginBottom: 20 }}>
        Comparing products…
      </p>

      <div className="loading-steps">
        {STEPS.map((step, i) => {
          const status =
            i < activeStep ? "done" : i === activeStep ? "active" : "";
          return (
            <div key={step.id} className={`loading-step ${status}`}>
              <div className="step-dot" />
              <span>
                {i < activeStep ? "✓ " : ""}{step.label}
              </span>
            </div>
          );
        })}
      </div>

      <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 20 }}>
        This may take up to 60 seconds for JS-heavy pages
      </p>
    </div>
  );
}
