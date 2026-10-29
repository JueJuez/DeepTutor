import assert from "node:assert/strict";
import test from "node:test";

import {
  bridgeEpubNonLinearTurn,
  directionForEpubLayout,
  hrefKey,
  locatorForEpubHref,
  resolveEpubPageTurnSwipe,
} from "../lib/epub-page-turn";

test("horizontal swipes turn pages but vertical scrolls do not", () => {
  assert.equal(resolveEpubPageTurnSwipe(200, 100, 100, 105), "next");
  assert.equal(resolveEpubPageTurnSwipe(100, 100, 200, 105), "previous");
  assert.equal(resolveEpubPageTurnSwipe(100, 100, 140, 100), null);
  assert.equal(resolveEpubPageTurnSwipe(100, 100, 160, 180), null);
});

test("RTL reverses physical rendition direction", () => {
  assert.equal(directionForEpubLayout("next", false), "next");
  assert.equal(directionForEpubLayout("next", true), "previous");
  assert.equal(directionForEpubLayout("previous", true), "next");
});

test("source hrefs map to the server locator despite encoding and base paths", () => {
  const refs = [
    { locator: 1, source_href: "OEBPS/chapters/one.xhtml" },
    { locator: 2, source_href: "OEBPS/chapters/two%20words.xhtml" },
  ];
  assert.equal(locatorForEpubHref("OEBPS/chapters/one.xhtml#p1", refs), 1);
  assert.equal(locatorForEpubHref("chapters/two words.xhtml", refs), 2);
  assert.equal(locatorForEpubHref("missing.xhtml", refs), 0);
  assert.equal(hrefKey("./chapter.xhtml#here"), "chapter.xhtml");
});

test("non-linear spine items bridge to the adjacent linear section", () => {
  const spine = [
    { href: "Text/cover_page.xhtml", index: 0, linear: false },
    { href: "Text/part0000.xhtml", index: 1, linear: true },
    { href: "Text/part0001.xhtml", index: 2, linear: true },
  ];
  assert.equal(
    bridgeEpubNonLinearTurn(spine, "Text/cover_page.xhtml", "next"),
    "Text/part0000.xhtml",
  );
  assert.equal(bridgeEpubNonLinearTurn(spine, "Text/cover_page.xhtml", "previous"), null);
});

test("consecutive non-linear items are skipped in one bridge", () => {
  const spine = [
    { href: "Text/part0000.xhtml", index: 0, linear: true },
    { href: "Text/part0001.xhtml", index: 1, linear: false },
    { href: "Text/part0002.xhtml", index: 2, linear: false },
    { href: "Text/part0003.xhtml", index: 3, linear: true },
  ];
  assert.equal(
    bridgeEpubNonLinearTurn(spine, "Text/part0001.xhtml", "next"),
    "Text/part0003.xhtml",
  );
  assert.equal(
    bridgeEpubNonLinearTurn(spine, "Text/part0002.xhtml", "previous"),
    "Text/part0000.xhtml",
  );
  assert.equal(bridgeEpubNonLinearTurn(spine, "Text/part0003.xhtml", "previous"), null);
});

test("linear sections and unknown hrefs keep the rendition's own turn", () => {
  const spine = [
    { href: "Text/cover_page.xhtml", index: 0, linear: false },
    { href: "Text/part0000.xhtml", index: 1, linear: true },
  ];
  assert.equal(bridgeEpubNonLinearTurn(spine, "Text/part0000.xhtml", "next"), null);
  assert.equal(bridgeEpubNonLinearTurn(spine, "Text/missing.xhtml", "next"), null);
  assert.equal(bridgeEpubNonLinearTurn(undefined, "Text/cover_page.xhtml", "next"), null);
  assert.equal(bridgeEpubNonLinearTurn(spine, undefined, "next"), null);
});
