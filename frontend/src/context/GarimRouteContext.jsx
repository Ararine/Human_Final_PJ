import { GarimRouteContext } from "./garimRouteContext";

export function GarimRouteProvider({ children, route }) {
  return (
    <GarimRouteContext.Provider value={route}>
      {children}
    </GarimRouteContext.Provider>
  );
}
