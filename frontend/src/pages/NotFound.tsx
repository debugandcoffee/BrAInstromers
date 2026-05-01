import { useLocation } from "react-router-dom";

export default function NotFound() {
  const location = useLocation();

  return (
    <div style={{ display: "grid", minHeight: "100vh", placeItems: "center", padding: 24, textAlign: "center" }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 56 }}>404</h1>
        <p style={{ color: "#475467" }}>No route exists for {location.pathname}</p>
      </div>
    </div>
  );
}
