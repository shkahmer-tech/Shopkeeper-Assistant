/**
 * Every call to the FastAPI backend lives in this file.
 * The backend address comes from VITE_API_URL (see .env).
 */
const BASE = ((import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const isForm = init.body instanceof FormData;
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      ...init,
      headers: isForm ? init.headers : { "Content-Type": "application/json", ...(init.headers ?? {}) },
    });
  } catch {
    throw new ApiError(`Cannot reach the backend at ${BASE}. Is it running?`, 0);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

const get = <T>(p: string) => request<T>(p);
const post = <T>(p: string, body?: unknown) =>
  request<T>(p, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
const upload = <T>(p: string, file?: File) => {
  const fd = new FormData();
  if (file) fd.append("file", file);
  return request<T>(p, { method: "POST", body: fd });
};

// ---------- types ----------
export interface Health {
  status: string;
  demand_model_trained: boolean;
  delivery_model_trained: boolean;
}
export interface OrderItem {
  name: string;
  quantity: number;
  unit_price: number;
  unit_weight_kg: number;
}
export interface OrderItemStatus extends OrderItem {
  delivered: boolean;
}
export interface Driver {
  driver_id: string;
  name: string;
  phone: string;
  vehicle_type: string;
  status: string;
  max_items?: number;
  max_weight_kg?: number;
}
export interface Order {
  tracking_id: string;
  status: string;
  distance_km: number;
  traffic_level: number;
  items: OrderItemStatus[];
  total_items: number;
  total_weight_kg: number;
  total_price: number;
  items_delivered: number;
  items_remaining: number;
  estimated_minutes: number;
  remaining_minutes: number;
  driver: Driver;
  created_at: string;
  updated_at: string;
  actual_minutes: number | null;
}
export interface Forecast {
  reference_date: string;
  predicted_daily: number;
  predicted_weekly: number;
  predicted_monthly: number;
}
export interface InventoryCheck {
  category: string | null;
  current_stock: number;
  weekly_demand: number;
  monthly_demand: number;
  status: string;
  reorder_units: number;
  action_note: string;
}
export interface DeliveryPrediction {
  distance_km: number;
  traffic_level: number;
  estimated_minutes: number;
  total_items: number;
  total_weight_kg: number;
  total_price: number;
}
export interface TrainResult {
  rows_used: number;
  features_used: string[];
  message: string;
  mae?: number;
  mae_minutes?: number;
  r2_score: number;
}
export interface FullReport {
  demand: Forecast;
  inventory: InventoryCheck;
  delivery: DeliveryPrediction;
  chart_path?: string | null;
  ai_review?: string | null;
}

// ---------- endpoints ----------
export const api = {
  health: () => get<Health>("/api/health"),

  categories: {
    list: () => get<{ categories: string[] }>("/api/categories"),
    add: (name: string, initial_stock: number) =>
      post<{ categories: string[]; message?: string }>("/api/categories/add", { name, initial_stock }),
    remove: (name: string) => post<{ categories: string[] }>("/api/categories/remove", { name }),
  },

  inventory: {
    stock: () => get<{ stock: Record<string, number>; total_stock: number }>("/api/inventory/stock"),
    setStock: (category: string, current_stock: number) =>
      post<{ message: string }>("/api/inventory/set-stock", { category, current_stock }),
    sell: (category: string, units_sold: number, add_to_training_data: boolean) =>
      post<{ message: string }>("/api/inventory/sell", { category, units_sold, add_to_training_data }),
    check: (category?: string, target_date?: string) =>
      post<InventoryCheck>("/api/inventory/check", { category, target_date }),
  },

  orders: {
    list: () => get<Record<string, Order>>("/api/orders"),
    track: (id: string) => get<Order>(`/api/orders/${id}`),
    create: (distance_km: number, traffic_level: number, items: OrderItem[]) =>
      post<Order>("/api/orders/create", { distance_km, traffic_level, items }),
    status: (id: string, status: string, actual_minutes?: number, delivered_items?: string[]) =>
      post<Order>(`/api/orders/${id}/status`, { status, actual_minutes, delivered_items }),
  },

  drivers: { list: () => get<Driver[]>("/api/drivers") },

  delivery: {
    train: (file?: File) => upload<TrainResult>("/api/delivery/train", file),
    predict: (distance_km: number, traffic_level: number, items: OrderItem[]) =>
      post<DeliveryPrediction>("/api/delivery/predict", { distance_km, traffic_level, items }),
  },

  demand: {
    train: (file?: File) => upload<TrainResult>("/api/demand/train", file),
    forecast: (target_date: string) => post<Forecast>("/api/demand/forecast", { target_date }),
    addRecord: (record: Record<string, unknown>, retrain: boolean) =>
      post<{ message: string }>("/api/demand/add-record", { record, retrain }),
  },

  report: {
    full: (p: {
      target_date: string;
      distance_km: number;
      traffic_level: number;
      items: OrderItem[];
      include_ai_review: boolean;
    }) => post<FullReport>("/api/report/full", p),
  },
};
