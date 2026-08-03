import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import { SignupForm } from "./components/auth/SignupForm";
import { ActivateAccount } from "./components/auth/ActivateAccount";
import Login from "./components/auth/Login";
import Dashboard from "./components/dashboard/Dashboard";
import { AuthContext, AuthProvider } from "./contexts/AuthContext";
import { MenuContext, MenuContextProvider } from "./contexts/MenuContext";
import { useContext } from "react";

export default function App() {
  const isSessionActive = useContext(AuthContext);
  const [currentMenu] = useContext(MenuContext);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public pages - no authentication check */}
        <Route
          path="/login"
          element={
            !isSessionActive ? (
              <Login />
            ) : (
              <Navigate to={`/dashboard/${currentMenu}`} replace />
            )
          }
        />
        <Route path="/register" element={<SignupForm />} />
        <Route path="/account/confirm" element={<ActivateAccount />} />

        {/* Protected pages - wrapped with authentication context provider */}
        <Route
          element={
            <AuthProvider>
              <Outlet />
            </AuthProvider>
          }
        >
          <Route
            path="/"
            element={<Navigate to="/dashboard/projects" replace />}
          />
          <Route
            element={
              <MenuContextProvider>
                <Outlet />
              </MenuContextProvider>
            }
          >
            <Route path="/dashboard/:menu" element={<Dashboard />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
