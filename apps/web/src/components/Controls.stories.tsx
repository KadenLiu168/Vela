import { FeedbackMessage } from "./FeedbackMessage";

/** Applicable button states across the three-variant contract. */
export const ButtonsDefault = () => (
  <div className="operation-list">
    <button className="button-primary" type="button">
      Primary action
    </button>
    <button className="button-secondary" type="button">
      Secondary action
    </button>
    <button className="button-tertiary" type="button">
      Tertiary action
    </button>
  </div>
);

export const ButtonsPending = () => (
  <div className="operation-list">
    {/* Pending buttons keep their full operation text; no width collapse. */}
    <button className="button-primary" disabled type="button">
      Running bootstrap / Setup database & data
    </button>
    <button className="button-secondary" disabled type="button">
      Running backtest
    </button>
  </div>
);

export const ButtonsDisabled = () => (
  <div className="operation-list">
    <button className="button-primary" disabled type="button">
      Primary disabled
    </button>
    <button className="button-secondary" disabled type="button">
      Secondary disabled
    </button>
    <button className="button-tertiary" disabled type="button">
      Tertiary disabled
    </button>
  </div>
);

export const ButtonsSelected = () => (
  <div className="signal-source-filter">
    <button aria-pressed="true" className="button-secondary" type="button">
      Manual
    </button>
    <button aria-pressed="false" className="button-secondary" type="button">
      Scheduled
    </button>
  </div>
);

/** Input states: default, invalid with an associated error, disabled. */
export const Inputs = () => (
  <form className="backtest-run-form">
    <label>
      <span>Start date</span>
      <input placeholder="YYYY-MM-DD" type="text" />
    </label>
    <label>
      <span>End date</span>
      <input
        aria-describedby="controls-story-date-error"
        aria-invalid="true"
        placeholder="YYYY-MM-DD"
        type="text"
      />
    </label>
    <FeedbackMessage variant="error">
      <span id="controls-story-date-error">Enter dates in YYYY-MM-DD format.</span>
    </FeedbackMessage>
    <label>
      <span>Disabled input</span>
      <input disabled placeholder="YYYY-MM-DD" type="text" />
    </label>
  </form>
);

/** Selector states on the detail rolling-diagnostics select. */
export const Selector = () => (
  <div className="stability-select">
    <label htmlFor="selector-story-window">Rolling window</label>
    <select id="selector-story-window" defaultValue="63">
      <option value="63">63 sessions</option>
      <option value="126">126 sessions</option>
      <option value="252">252 sessions</option>
    </select>
  </div>
);
