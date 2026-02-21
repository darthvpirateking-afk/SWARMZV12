import { Outlet } from "react-router-dom";
import { CockpitTopBar } from "../components/CockpitTopBar";
import { SideNav } from "../components/SideNav";
import { ErrorBoundary } from "../components/ErrorBoundary";

export default function CockpitLayout() {
  return (
    <div className="min-h-screen bg-cosmic-bg text-cosmic-text-primary font-sans grid grid-rows-[auto_1fr]">
      <CockpitTopBar buildTag="v12.0" />

      <div className="flex">
        <SideNav />

        <main className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-[960px] mx-auto w-full grid gap-5">
            <ErrorBoundary>
              <Outlet />
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
}
