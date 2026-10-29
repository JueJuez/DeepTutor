import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReaderPane } from "@/components/reading/ReaderPane";
import { initI18n } from "@/i18n/init";

initI18n("en");

const material = {
  material_id: "m-1",
  title: "A Book",
  render_mode: "text",
  unit: "section",
  unit_count: 200,
  unit_refs: [],
  has_raw_view: false,
  status: "ready",
  source_kind: "upload",
  extractor: "",
};

vi.mock("@/context/ReadingContext", () => ({
  useReading: () => ({
    material,
    annotations: [],
    loading: false,
    error: "",
    openMaterial: vi.fn(),
    closeMaterial: vi.fn(),
    saveMark: vi.fn(),
    removeMark: vi.fn(),
    mergeMark: vi.fn(),
    dismissError: vi.fn(),
    setError: vi.fn(),
    reportViewport: vi.fn(),
  }),
}));

// The text view reports its opening locator the moment it mounts, exactly
// like the real document views do; the latest jump request is captured so a
// test can assert what the reader asked the view to scroll to.
let latestJump: { locator: number } | null = null;
vi.mock("@/components/reading/TextUnitView", () => ({
  unitLabel: () => "section",
  TextUnitView: ({
    jump,
    onVisibleLocatorChange,
  }: {
    jump?: { locator: number } | null;
    onVisibleLocatorChange?: (locator: number) => void;
  }) => {
    latestJump = jump ?? null;
    React.useEffect(() => {
      onVisibleLocatorChange?.(1);
      // Test double: the reporting callback identity is irrelevant here.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    return (
      <button
        type="button"
        onClick={() => onVisibleLocatorChange?.(5)}
      >
        turn to section 5
      </button>
    );
  },
}));
vi.mock("@/components/reading/PdfDocumentView", () => ({
  PdfDocumentView: () => null,
}));
vi.mock("@/components/reading/EpubDocumentView", () => ({
  EpubDocumentView: () => null,
}));

const getReadingPosition = vi.fn<(materialId: string) => Promise<unknown>>();
const saveReadingPosition = vi.fn<
  (
    materialId: string,
    position: { locator: number; source_anchor: string; percentage?: number },
  ) => Promise<unknown>
>(async () => {});
vi.mock("@/lib/reading-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/reading-api")>();
  return {
    ...actual,
    getReadingPosition: (
      ...args: Parameters<typeof actual.getReadingPosition>
    ) => getReadingPosition(...args),
    saveReadingPosition: (
      ...args: Parameters<typeof actual.saveReadingPosition>
    ) => saveReadingPosition(...args),
  };
});

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

describe("reading position resume", () => {
  it("does not save the opening locator before the stored position is read", async () => {
    latestJump = null;
    let resolvePosition: (position: unknown) => void = () => {};
    getReadingPosition.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePosition = resolve;
        }),
    );

    render(<ReaderPane onClose={vi.fn()} />);
    await screen.findByText("turn to section 5");

    // The view reported page 1 on mount; the debounced save must not fire
    // while the resume is still reading the stored position, or it would
    // overwrite the progress the resume is about to restore.
    await wait(550);
    expect(saveReadingPosition).not.toHaveBeenCalled();

    resolvePosition({ locator: 100, source_anchor: "", percentage: 0.5, updated_at: 1 });
    await waitFor(() => expect(latestJump).toMatchObject({ locator: 100 }));

    // After the resume settles, scrolling saves normally.
    fireEvent.click(screen.getByText("turn to section 5"));
    await waitFor(() =>
      expect(saveReadingPosition).toHaveBeenCalledWith(
        "m-1",
        expect.objectContaining({ locator: 5 }),
      ),
    );
  });

  it("saves normally once the stored position has been read", async () => {
    latestJump = null;
    getReadingPosition.mockResolvedValue({
      locator: 1,
      source_anchor: "",
      percentage: 0,
      updated_at: 1,
    });

    render(<ReaderPane onClose={vi.fn()} />);
    await screen.findByText("turn to section 5");

    fireEvent.click(screen.getByText("turn to section 5"));
    await waitFor(() =>
      expect(saveReadingPosition).toHaveBeenCalledWith(
        "m-1",
        expect.objectContaining({ locator: 5 }),
      ),
    );
    expect(latestJump).toBeNull();
  });
});
