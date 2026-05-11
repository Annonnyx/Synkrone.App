"use client";

import { useEffect } from "react";

/**
 * Removes browser-extension injected attributes that cause React hydration mismatches.
 * Runs once after mount to clean up any `bis_skin_checked` or similar attrs.
 */
export default function CleanExtensionAttrs() {
  useEffect(() => {
    const EXT_ATTRS = ["bis_skin_checked", "bis_register", "__mapped"] as const;

    function clean(node: Element) {
      EXT_ATTRS.forEach((attr) => {
        if (node.hasAttribute(attr)) {
          node.removeAttribute(attr);
        }
      });
    }

    // Clean existing nodes
    document.querySelectorAll(`[${EXT_ATTRS.join("],[")}]`).forEach(clean);

    // Observe future mutations
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((n) => {
          if (n instanceof Element) {
            clean(n);
            n.querySelectorAll(`[${EXT_ATTRS.join("],[")}]`).forEach(clean);
          }
        });
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);

  return null;
}
