import { Navigate, Route, Routes } from "react-router-dom";
import Home from "@/pages/home/page";
import NotFound from "@/pages/NotFound";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/home" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
