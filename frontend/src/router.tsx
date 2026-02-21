import { createBrowserRouter, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import CockpitLayout from "./layouts/CockpitLayout";
import App from "./App";

// Lazy-loaded pages — using named exports via .then() remapping
const Bootstrap = lazy(() =>
  import("./pages/BootstrapPage").then((m) => ({ default: m.BootstrapPage })),
);
const ApiFoundation = lazy(() =>
  import("./pages/ApiFoundationPage").then((m) => ({
    default: m.ApiFoundationPage,
  })),
);
const Milestones = lazy(() =>
  import("./pages/BuildMilestonesPage").then((m) => ({
    default: m.BuildMilestonesPage,
  })),
);
const Companion = lazy(() =>
  import("./pages/CompanionCorePage").then((m) => ({
    default: m.CompanionCorePage,
  })),
);
const Database = lazy(() =>
  import("./pages/DatabaseLayerPage").then((m) => ({
    default: m.DatabaseLayerPage,
  })),
);
const Auth = lazy(() =>
  import("./pages/OperatorAuthPage").then((m) => ({
    default: m.OperatorAuthPage,
  })),
);

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-pulse text-cosmic-text-secondary">Loading...</div>
    </div>
  );
}

function LazyPage({
  Component,
}: {
  Component: React.LazyExoticComponent<React.ComponentType>;
}) {
  return (
    <Suspense fallback={<PageLoader />}>
      <Component />
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <CockpitLayout />,
    children: [
      { index: true, element: <App /> },
      { path: "bootstrap", element: <LazyPage Component={Bootstrap} /> },
      {
        path: "api-foundation",
        element: <LazyPage Component={ApiFoundation} />,
      },
      { path: "milestones", element: <LazyPage Component={Milestones} /> },
      { path: "companion", element: <LazyPage Component={Companion} /> },
      { path: "database", element: <LazyPage Component={Database} /> },
      { path: "auth", element: <LazyPage Component={Auth} /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
