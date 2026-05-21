import GarimFooter from "./GarimFooter";
import GarimHeader from "./GarimHeader";
import { useGarimRoute } from "../../hooks/useGarimRoute";
import { getDefaultBodyClass, getHeaderLayout } from "../../utils/garimLayout";

export default function GarimPage({
  children,
  bodyClass,
  screenLabel,
}) {
  const route = useGarimRoute();
  const layout = route?.layout ?? "public";
  const current = route?.current ?? "";
  const headerLayout = getHeaderLayout(layout, current);

  return (
    <div className={bodyClass ?? getDefaultBodyClass(layout)} data-screen-label={screenLabel ?? route?.name ?? ""}>
      <GarimHeader layout={headerLayout} current={current} />
      {children}
      <GarimFooter minimal={layout === "auth"} />
    </div>
  );
}
