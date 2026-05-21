export function getHeaderLayout(layout, current) {
  return layout === "public" && current === "landing" ? "landing" : layout;
}

export function getDefaultBodyClass(layout) {
  if (layout === "auth") return "page-auth";
  if (layout === "app") return "page-app";
  return "page-public";
}
