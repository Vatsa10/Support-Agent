import { redirect } from "next/navigation";
import { Sidebar } from "@/components/app/Sidebar";
import { backendFetchSafe, getSession } from "@/lib/api-server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = getSession();
  if (!session) redirect("/signin");

  const me = await backendFetchSafe<any>("/auth/me");
  if (!me || me.error) redirect("/signin");

  return (
    <div className="min-h-dvh flex bg-cream">
      <Sidebar tenantName={me.tenant_name} tenantId={me.tenant_id} userEmail={me.user?.email} />
      <div className="flex-1 min-w-0 bg-paper border-l border-line">{children}</div>
    </div>
  );
}
