import { useState } from "react";
import { Boxes, Clock, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, type FullReport, type OrderItem } from "@/lib/api";
import { ItemsEditor } from "@/components/items-editor";
import { Badge, Field, Notice, PageHeader, Panel, StatCard, fmt, inputCls, today, useAction } from "@/components/ui-bits";

export default function Report() {
  const [date, setDate] = useState(today());
  const [distance, setDistance] = useState("8");
  const [traffic, setTraffic] = useState("5");
  const [items, setItems] = useState<OrderItem[]>([]);
  const [ai, setAi] = useState(true);
  const [report, setReport] = useState<FullReport | null>(null);
  const { busy, msg, run } = useAction();

  return (
    <>
      <PageHeader title="Full Report" subtitle="Demand forecast, inventory status and delivery estimate in one go." />
      <Panel title="Report Inputs" className="max-w-3xl">
        <form
          className="flex flex-col gap-4"
          onSubmit={async (e) => {
            e.preventDefault();
            const r = await run(() =>
              api.report.full({
                target_date: date,
                distance_km: Number(distance),
                traffic_level: Number(traffic),
                items: items.filter((i) => i.name.trim()),
                include_ai_review: ai,
              }),
            );
            if (r) setReport(r);
          }}
        >
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Field label="Date">
              <input className={inputCls} type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </Field>
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
          <ItemsEditor items={items} onChange={setItems} />
          <label className="text-muted-foreground flex items-center gap-2 text-sm">
            <input type="checkbox" checked={ai} onChange={(e) => setAi(e.target.checked)} /> Include AI review
          </label>
          <Button type="submit" className="h-11" disabled={busy}>
            {busy ? "Generating..." : "Generate report"}
          </Button>
          <Notice msg={msg} />
        </form>
      </Panel>

      {report && (
        <div className="mt-8 flex flex-col gap-8">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <StatCard
              icon={TrendingUp}
              iconClass="text-[#3B82F6]"
              label="Monthly demand"
              value={fmt(report.demand.predicted_monthly, 0)}
              note={`weekly ${fmt(report.demand.predicted_weekly, 0)} · daily ${fmt(report.demand.predicted_daily, 0)}`}
            />
            <StatCard
              icon={Boxes}
              iconClass="text-[#A855F7]"
              label="Current stock"
              value={fmt(report.inventory.current_stock, 0)}
              note={`reorder ${report.inventory.reorder_units} units`}
            />
            <StatCard
              icon={Clock}
              iconClass="text-[#22C55E]"
              label="Delivery estimate"
              value={`${fmt(report.delivery.estimated_minutes)} min`}
              note={`${report.delivery.total_items} items · ${fmt(report.delivery.total_weight_kg, 2)} kg`}
            />
          </div>
          <Panel title="Inventory Status">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge
                tone={
                  report.inventory.status.includes("CRITICALLY")
                    ? "bad"
                    : report.inventory.status.includes("1 week")
                      ? "warn"
                      : "ok"
                }
              >
                {report.inventory.status}
              </Badge>
              <span>{report.inventory.action_note}</span>
            </div>
          </Panel>
          {report.ai_review && (
            <Panel title="AI Review">
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{report.ai_review}</p>
            </Panel>
          )}
        </div>
      )}
    </>
  );
}
