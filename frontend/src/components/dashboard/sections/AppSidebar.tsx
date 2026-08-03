import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/shadcn/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/shadcn/sidebar";
import useAPIOnMount from "@/lib/hooks/api";
import { getFromLocalStorage } from "@/lib/utils";
import { UserOrgs } from "@/schemas/organizations";
import { ChevronsUpDown, Folder, Rocket } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function AppSidebar() {
  const { isMobile, setOpenMobile } = useSidebar();
  const navigate = useNavigate();
  const [user_id] = useState<string | null>(() => {
    return getFromLocalStorage("user_id");
  });
  const [email] = useState<string | null>(() => {
    return getFromLocalStorage("email");
  });

  const [response] = useAPIOnMount(`${API_URL}/orgs/${user_id}`, UserOrgs);
  const organizations: string[] = response?.organizations ?? [];

  return (
    <Sidebar variant="floating" collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild className="cursor-pointer">
                <SidebarMenuButton size="lg">
                  <img
                    src="/deplocker.png"
                    className="size-8 rounded-md object-contain"
                  />
                  <span className="truncate">{organizations[0]}</span>
                  <ChevronsUpDown className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="right"
                align="start"
                className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
              >
                {organizations.map((org, index) => (
                  <DropdownMenuItem key={index}>
                    <span>{org}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Home</SidebarGroupLabel>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Projects"
              onClick={() => {
                if (isMobile) setOpenMobile(false);
                navigate("/dashboard/projects");
              }}
            >
              <Folder />
              <span>Projects</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Deployments"
              onClick={() => {
                if (isMobile) setOpenMobile(false);
                navigate("/dashboard/deployments");
              }}
            >
              <Rocket />
              <span>Deployments</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <div className="flex gap-1">
          <span className="relative flex shrink-0 overflow-hidden h-8 w-8 rounded-lg">
            <span className="flex h-full w-full items-center justify-center bg-[rgb(66,121,53)] rounded-lg text-white">
              {email?.[0].toUpperCase()}
            </span>
          </span>
          <div className="flex flex-col">
            <span className="truncate font-semibold">Account</span>
            <span className="truncate text-sm">{email}</span>
          </div>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
