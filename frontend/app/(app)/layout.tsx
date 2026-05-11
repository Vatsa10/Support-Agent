import { Sidebar } from "@/components/app/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh flex bg-cream">
      <Sidebar />
      <div className="flex-1 min-w-0 bg-paper border-l border-line">{children}</div>
    </div>
  );
}
