import { Bike, Car, Phone } from "lucide-react";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Badge, Notice, PageHeader, fmt, useAsync } from "@/components/ui-bits";

export default function Drivers() {
  const drivers = useAsync(api.drivers.list);

  return (
    <>
      <PageHeader title="Drivers" subtitle="Your riders and how much each vehicle can carry." />
      {drivers.error && <Notice msg={{ kind: "err", text: drivers.error }} />}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {(drivers.data ?? []).map((d) => {
          const Icon = d.vehicle_type.toLowerCase() === "car" ? Car : Bike;
          return (
            <Card key={d.driver_id} className="bg-secondary gap-4 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="bg-background flex size-11 items-center justify-center rounded-lg">
                    <Icon className="size-5" />
                  </div>
                  <div>
                    <p className="font-medium">{d.name}</p>
                    <p className="text-muted-foreground text-xs">
                      {d.driver_id} · {d.vehicle_type}
                    </p>
                  </div>
                </div>
                <Badge tone={d.status === "available" ? "ok" : "warn"}>{d.status}</Badge>
              </div>
              <p className="text-muted-foreground flex items-center gap-2 text-sm">
                <Phone className="size-4" />
                {d.phone}
              </p>
              <p className="text-sm">
                Carries up to <b>{d.max_items ?? "—"}</b> items / <b>{fmt(d.max_weight_kg, 0)}</b> kg
              </p>
            </Card>
          );
        })}
      </div>
    </>
  );
}
