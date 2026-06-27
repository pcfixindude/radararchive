import type { AccessCurrentInfo, DemoPlan } from '../api/client';
import { DEMO_PLANS } from '../api/client';

export default function PlanSelector({
  plan,
  accessInfo,
  onChange,
}: {
  plan: DemoPlan;
  accessInfo: AccessCurrentInfo | null;
  onChange: (plan: DemoPlan) => void;
}) {
  return (
    <section className="panel plan-panel">
      <h2>Demo Plan</h2>
      <p className="plan-note">Stub subscription selector — not real Stripe billing.</p>
      <label>
        Selected plan
        <select value={plan} onChange={(event) => onChange(event.target.value as DemoPlan)}>
          {DEMO_PLANS.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      {accessInfo ? (
        <>
          <p className="plan-meta">History limit: {accessInfo.history_limit_label}</p>
          <p className="plan-meta">Reference latest: {accessInfo.reference_latest ?? '—'}</p>
          <p className="plan-upgrade">{accessInfo.upgrade_message}</p>
        </>
      ) : null}
    </section>
  );
}
