import { useState } from "react";
import { CalendarDays, CalendarRange, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, type Forecast } from "@/lib/api";
import { Field, Notice, PageHeader, Panel, StatCard, fmt, inputCls, today, useAction } from "@/components/ui-bits";

export default function Demand() {
  const [file, setFile] = useState<File | undefined>();
  const [date, setDate] = useState(today());
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [recDate, setRecDate] = useState(today());
  const [units, setUnits] = useState("");
  const [extra, setExtra] = useState("");
  const [retrain, setRetrain] = useState(true);
  const train = useAction();
  const fc = useAction();
  const add = useAction();

  return (
    <>
      <PageHeader title="Demand" subtitle="Forecast how many units you will sell." />
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <Panel title="Train Model">
          <div className="flex flex-col gap-3">
            <p className="text-muted-foreground text-sm">
              Leave the file empty to train on your saved sales data, or upload a CSV to merge into it.
            </p>
            <input type="file" accept=".csv" className="text-sm" onChange={(e) => setFile(e.target.files?.[0])} />
            <Button
              className="h-11"
              disabled={train.busy}
              onClick={() =>
                train.run(
                  () => api.demand.train(file),
                  (r) => `${r.message} Rows: ${r.rows_used}, MAE: ${fmt(r.mae, 2)}, R²: ${fmt(r.r2_score, 3)}`,
                )
              }
            >
              {train.busy ? "Training..." : "Train demand model"}
            </Button>
            <Notice msg={train.msg} />
          </div>
        </Panel>

        <Panel title="Forecast">
          <div className="flex flex-col gap-3">
            <Field label="Date">
              <input className={inputCls} type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </Field>
            <Button
              className="h-11"
              disabled={fc.busy}
              onClick={async () => {
                const r = await fc.run(() => api.demand.forecast(date));
                if (r) setForecast(r);
              }}
            >
              Forecast
            </Button>
            <Notice msg={fc.msg} />
          </div>
        </Panel>
      </div>

      {forecast && (
        <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatCard
            icon={Sun}
            iconClass="text-[#F59E0B]"
            label="Daily"
            value={fmt(forecast.predicted_daily, 0)}
            note={`from ${forecast.reference_date}`}
          />
          <StatCard icon={CalendarDays} iconClass="text-[#3B82F6]" label="Weekly" value={fmt(forecast.predicted_weekly, 0)} />
          <StatCard
            icon={CalendarRange}
            iconClass="text-[#A855F7]"
            label="Monthly"
            value={fmt(forecast.predicted_monthly, 0)}
          />
        </div>
      )}

      <Panel title="Add a Real Sale" className="mt-8 max-w-xl">
        <form
          className="flex flex-col gap-3"
          onSubmit={async (e) => {
            e.preventDefault();
            let more: Record<string, unknown> = {};
            if (extra.trim()) {
              try {
                more = JSON.parse(extra);
              } catch {
                add.setMsg({ kind: "err", text: "Extra fields must be valid JSON" });
                return;
              }
            }
            // Column names must match your demand CSV ("Date" and "Units Sold" are your defaults)
            await add.run(
              () => api.demand.addRecord({ Date: recDate, "Units Sold": Number(units), ...more }, retrain),
              (r) => r.message,
            );
          }}
        >
          <div className="grid grid-cols-2 gap-3">
            <Field label="Date">
              <input className={inputCls} type="date" value={recDate} onChange={(e) => setRecDate(e.target.value)} />
            </Field>
            <Field label="Units sold">
              <input
                className={inputCls}
                type="number"
                min={0}
                value={units}
                onChange={(e) => setUnits(e.target.value)}
                required
              />
            </Field>
          </div>
          <Field label='Extra columns (optional JSON, e.g. {"Product ID": "P1"})'>
            <input
              className={inputCls}
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
              placeholder='{"Product ID": "P1"}'
            />
          </Field>
          <label className="text-muted-foreground flex items-center gap-2 text-sm">
            <input type="checkbox" checked={retrain} onChange={(e) => setRetrain(e.target.checked)} /> Retrain the model now
          </label>
          <Button type="submit" className="h-11" disabled={add.busy || !units}>
            Add record
          </Button>
          <Notice msg={add.msg} />
        </form>
      </Panel>
    </>
  );
}
