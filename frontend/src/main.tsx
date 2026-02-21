import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { Toaster } from "sonner";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import { router } from "./router";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <WebSocketProvider>
      <RouterProvider router={router} />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#0C1020",
            border: "1px solid #1E2A40",
            color: "#F5F7FF",
          },
        }}
      />
    </WebSocketProvider>
  </StrictMode>,
);
