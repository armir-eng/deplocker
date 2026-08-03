import ErrorPage from "@/components/dashboard/sections/ErrorPage";
import { DashboardMenu } from "@/schemas/dashboard";
import React from "react";
import { useParams } from "react-router-dom";
import { InferType, ValidationError } from "yup";

export const MenuContext = React.createContext<
  [
    InferType<typeof DashboardMenu>,
    React.Dispatch<React.SetStateAction<InferType<typeof DashboardMenu>>>,
  ]
>(["projects", () => {}]);

export function MenuContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { menu } = useParams();

  // The active menu is derived directly from the URL param, which is the single
  // source of truth. An invalid param renders the error page.
  let activeMenu: InferType<typeof DashboardMenu>;
  try {
    activeMenu = DashboardMenu.validateSync(menu);
  } catch (error) {
    if (error instanceof ValidationError) {
      return <ErrorPage />;
    }
    throw error;
  }

  return (
    <MenuContext.Provider value={[activeMenu, () => {}]}>
      {children}
    </MenuContext.Provider>
  );
}
