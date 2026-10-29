import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PdfDocumentView } from "@/components/reading/PdfDocumentView";
import { initI18n } from "@/i18n/init";

initI18n("en");

// The document proxy resolves a beat after mount, the way a network PDF does.
const pendingDocResolvers: Array<(doc: unknown) => void> = [];
const fakeDoc = {
  numPages: 599,
  getPage: async () => ({
    getViewport: () => ({ width: 800, height: 1131 }),
  }),
};
vi.mock("@/lib/pdfjs-loader", () => ({
  loadPdfjs: async () => ({
    getDocument: () => ({
      promise: new Promise((resolve) => {
        pendingDocResolvers.push(resolve);
      }),
      destroy: async () => {},
    }),
  }),
  pdfjsWasmUrl: () => "/wasm/",
}));
vi.mock("@/components/reading/PdfPage", () => ({
  PdfPage: ({
    locator,
    width,
    fallbackRatio,
    active,
  }: {
    locator: number;
    width: number;
    fallbackRatio: number;
    active: boolean;
  }) => (
    <div
      data-reader-unit={locator}
      data-active={active ? "true" : "false"}
      style={{ width, height: Math.round(width * fallbackRatio) }}
    >
      page {locator}
    </div>
  ),
}));

const annotations: never[] = [];

function renderView(jump: { locator: number; nonce: number } | null) {
  return render(
    <div style={{ width: 800, height: 600 }}>
      <PdfDocumentView
        materialId="m-1"
        unitCount={599}
        annotations={annotations}
        jump={jump}
        onVisibleLocatorChange={vi.fn()}
        onSelection={vi.fn()}
      />
    </div>,
  );
}

const deliverDoc = async () => {
  await new Promise((resolve) => setTimeout(resolve, 0));
  for (const resolve of pendingDocResolvers.splice(0)) resolve(fakeDoc);
};

describe("PdfDocumentView jump while the document is still loading", () => {
  it("honours a jump requested before the document arrives", async () => {
    // The resume requests the jump before the document proxy resolves —
    // exactly the reload sequence: position read → requestJump → raw loads.
    // jsdom has no layout, so the observable contract is the render window:
    // the target page must become active once the document lands.
    renderView({ locator: 100, nonce: 1 });
    await deliverDoc();

    const page = await screen.findByText("page 100");
    await waitFor(() => expect(page.closest("[data-active]")).toHaveAttribute("data-active", "true"));
  });

  it("honours a jump requested after the document is ready", async () => {
    const view = renderView(null);
    await deliverDoc();
    await screen.findByText("page 1");

    view.rerender(
      <div style={{ width: 800, height: 600 }}>
        <PdfDocumentView
          materialId="m-1"
          unitCount={599}
          annotations={annotations}
          jump={{ locator: 100, nonce: 2 }}
          onVisibleLocatorChange={vi.fn()}
          onSelection={vi.fn()}
        />
      </div>,
    );

    const page = await screen.findByText("page 100");
    await waitFor(() => expect(page.closest("[data-active]")).toHaveAttribute("data-active", "true"));
  });
});
