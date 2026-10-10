import { useState } from "react";
import { Clock, Package, Scale } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, type DeliveryPrediction, type OrderItem } from "@/lib/api";
import { ItemsEditor } from "@/components/items-editor";
import { Field, Notice, PageHeader, Panel, StatCard, fmt, inputCls, useAction } from "@/components/ui-bits";

export default function Delivery() {
  const [file, setFile] = useState<File | undefined>();
  const [distance, setDistance] = useState("8");
  const [traffic, setTraffic] = useState("5");
  const [items, setItems] = useState<OrderItem[]>([]);
  const [result, setResult] = useState<DeliveryPrediction | null>(null);
  const train = useAction();
  const predict = useAction();

  return (
    <>
      <PageHeader title="Delivery" subtitle="Estimate delivery time from distance, traffic and the items being carried." />
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <Panel title="Train Model">
          <div className="flex flex-col gap-3">
            <p className="text-muted-foreground text-sm">
              Leave the file empty to train on your saved delivery data, or upload a CSV to add to it.
            </p>
            <input type="file" accept=".csv" className="text-sm" onChange={(e) => setFile(e.target.files?.[0])} />
            <Button
              className="h-11"
              disabled={train.busy}
              onClick={() =>
                train.run(
                  () => api.delivery.train(file),
                  (r) =>
                    `${r.message} Rows: ${r.rows_used}, MAE: ${fmt(r.mae_minutes ?? r.mae, 2)} min, R²: ${fmt(r.r2_score, 3)}`,
                )
              }
            >
              {train.busy ? "Training..." : "Train delivery model"}
            </Button>
            <Notice msg={train.msg} />
          </div>
        </Panel>

        <Panel title="Predict Delivery Time">
          <form
            className="flex flex-col gap-4"
            onSubmit={async (e) => {
              e.preventDefault();
              const r = await predict.run(() =>
                api.delivery.predict(Number(distance), Number(traffic), items.filter((i) => i.name.trim())),
              );
              if (r) setResult(r);
            }}
          >
            <div className="grid grid-cols-2 gap-3">
              <Field label="Distance (km)">
                <input
                  className={inputCls}
                  type="number"
                  min={0}
                  step="0.1"
                  value={distance}
                  onChange={(e) => setDistance(e.target.value)}
                />
              </Field>
              <Field label="Traffic level">
                <input
                  className={inputCls}
                  type="number"
                  min={0}
                  step="0.1"
                  value={traffic}
                  onChange={(e) => setTraffic(e.target.value)}
                />
              </Field>
            </div>
            <div>
              <span className="text-secondary-foreground/80 mb-2 block text-sm font-medium">Items (optional)</span>
              <ItemsEditor items={items} onChange={setItems} />
            </div>
            <Button type="submit" className="h-11" disabled={predict.busy}>
              Predict
            </Button>
            <Notice msg={predict.msg} />
          </form>
        </Panel>
      </div>

      {result && (
        <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatCard
            icon={Clock}
            iconClass="text-[#3B82F6]"
            label="Estimated time"
            value={`${fmt(result.estimated_minutes)} min`}
          />
          <StatCard
            icon={Package}
            iconClass="text-[#A855F7]"
            label="Items"
            value={fmt(result.total_items, 0)}
            note={`value ${fmt(result.total_price, 0)}`}
          />
          <StatCard
            icon={Scale}
            iconClass="text-[#22C55E]"
            label="Total weight"
            value={`${fmt(result.total_weight_kg, 2)} kg`}
          />
        </div>
      )}
    </>
  );
}
