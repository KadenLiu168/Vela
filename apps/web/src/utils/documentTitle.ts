import { useEffect } from "react";

const BRAND = "Vela Research";

export function formatDocumentTitle(pageIdentity: string): string {
  return `${pageIdentity} · ${BRAND}`;
}

/**
 * Sets the document title for the page that calls it. Pages are the only
 * place that knows their own identity, and detail pages are the only place
 * that knows which entity they are showing, so the title is declared here
 * rather than derived from the rendered `<h1>`.
 */
export function useDocumentTitle(pageIdentity: string): void {
  useEffect(() => {
    document.title = formatDocumentTitle(pageIdentity);
  }, [pageIdentity]);
}
