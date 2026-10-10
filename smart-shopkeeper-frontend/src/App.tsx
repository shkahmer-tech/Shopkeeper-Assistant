import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/layout";
import Dashboard from "./pages/dashboard";
import Inventory from "./pages/inventory";
import Orders from "./pages/orders";
import Delivery from "./pages/delivery";
import Drivers from "./pages/drivers";
import Demand from "./pages/demand";
import Report from "./pages/report";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="orders" element={<Orders />} />
          <Route path="delivery" element={<Delivery />} />
          <Route path="drivers" element={<Drivers />} />
          <Route path="demand" element={<Demand />} />
          <Route path="report" element={<Report />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
