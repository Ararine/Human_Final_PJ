import { useContext } from "react";

import { GarimRouteContext } from "../context/garimRouteContext";

export function useGarimRoute() {
  return useContext(GarimRouteContext);
}
