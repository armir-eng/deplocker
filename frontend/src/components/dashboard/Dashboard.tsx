import { useContext } from "react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
} from "../shadcn/breadcrumb";
import { Card } from "../shadcn/card";
import AppSidebar from "./sections/AppSidebar";
import { SidebarProvider, SidebarTrigger } from "../shadcn/sidebar";
import MainHeader from "./sections/MainHeader";
import { menus } from "./confs/main-header";
import { MenuContext } from "@/contexts/MenuContext";

export default function Dashboard() {
  const [activeMenu] = useContext(MenuContext);

  return (
    <SidebarProvider>
      <AppSidebar />

      <main className="flex flex-col w-full pr-2">
        <header className="flex items-center gap-2 p-2">
          <SidebarTrigger className="cursor-pointer" />
          <div className="shrink-0 bg-border w-px mr-2 h-4"></div>
          <Breadcrumb className="m-2 p-2">
            <BreadcrumbList>
              <BreadcrumbItem>
                <a href={`/dashboard/${activeMenu}`} className="capitalize">
                  {activeMenu}
                </a>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>
        <div className="border text-card-foreground shadow-sm rounded-xl">
          <Card className="rounded-xl bg-background shadow-md m-1.5">
            <MainHeader
              titleIcon={menus[activeMenu].titleIcon}
              title={menus[activeMenu].title}
              subtitle={menus[activeMenu].subtitle}
              actionButton={menus[activeMenu].actionButton}
            />
          </Card>
        </div>
      </main>
    </SidebarProvider>
  );
}
