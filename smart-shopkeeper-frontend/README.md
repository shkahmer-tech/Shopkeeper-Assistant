# Smart Shopkeeper – Frontend

React + TypeScript + Vite + Tailwind CSS v4 dashboard for the Smart Shopkeeper FastAPI backend.
Design follows the shadcn "library-dashboard" sample (red/white theme, collapsible sidebar,
metric cards, charts), with light and dark mode.

## Run it

1. Start your backend (from the backend folder):

   ```bash
   uvicorn app.main:app --reload
   ```

2. Start the frontend (from this folder):

   ```bash
   npm install
   npm run dev
   ```

3. Open http://localhost:5173

## Connect to the backend

The backend address is set in `.env`:

```
VITE_API_URL=http://127.0.0.1:8000
```

Change it if your API runs elsewhere, then restart `npm run dev`.
All API calls are in `src/lib/api.ts`. Your backend already allows CORS from any origin;
restrict `allow_origins` in `main.py` before deploying.

## First-run order

1. Delivery page → Train delivery model
2. Demand page → Train demand model
3. Inventory page → add categories with starting stock
4. Orders page → create an order with items

## Pages

| Route        | Backend endpoints used                                                       |
| ------------ | ---------------------------------------------------------------------------- |
| `/`          | health, inventory/stock, orders, drivers, demand/forecast                    |
| `/inventory` | categories add/remove, inventory stock / set-stock / sell / check           |
| `/orders`    | orders create / list / status (with delivered items)                         |
| `/delivery`  | delivery train / predict                                                     |
| `/drivers`   | drivers                                                                      |
| `/demand`    | demand train / forecast / add-record                                         |
| `/report`    | report/full (demand + inventory + delivery + AI review)                      |

## Build for production

```bash
npm run build      # output in dist/
npm run preview
```
