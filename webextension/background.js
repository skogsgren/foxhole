const pdfTabs = new Set();

function getHeader(headers, name) {
  return headers.find(
    (h) => h.name && h.name.toLowerCase() === name.toLowerCase(),
  );
}

browser.webRequest.onHeadersReceived.addListener(
  async (details) => {
    const contentType = getHeader(
      details.responseHeaders || [],
      "content-type",
    );
    if (!contentType) return;

    if (/application\/pdf/i.test(contentType.value || "")) {
      console.log("Foxhole detected pdf:", details.url);

      pdfTabs.add(details.tabId);

      try {
        const response = await browser.runtime.sendNativeMessage(
          "foxhole_host",
          {
            kind: "pdf",
            url: details.url,
            tabId: details.tabId,
          },
        );
        console.log("Host replied for PDF:", response);
      } catch (err) {
        console.error("Foxhole native messaging error:", err);
      }
    }
  },
  { urls: ["<all_urls>"], types: ["main_frame"] },
  ["responseHeaders"],
);

browser.tabs.onRemoved.addListener((tabId) => {
  pdfTabs.delete(tabId);
});

browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !tab.url) return;

  if (pdfTabs.has(tabId)) {
    console.log("Skipping script injection for PDF tab:", tab.url);
    return;
  }

  if (
    tab.url.startsWith("about:") ||
    tab.url.startsWith("moz-extension:") ||
    tab.url.startsWith("view-source:")
  ) {
    return;
  }

  console.log("Tab updated, injecting script into:", tab.url);

  browser.tabs
    .executeScript(tabId, {
      code: `
      console.log("Foxhole content script executing on", window.location.href);
      browser.runtime.sendMessage({
        kind: "html",
        title: document.title,
        text: document.body ? document.body.innerText : "",
        url: window.location.href
      }).catch(err => console.error("Foxhole sendMessage failed:", err));
    `,
    })
    .catch((err) => {
      console.error("Foxhole script injection failed:", err);
    });
});

browser.runtime.onMessage.addListener((message, sender) => {
  return browser.runtime
    .sendNativeMessage("foxhole_host", message)
    .then((response) => {
      console.log("Foxhole native message response:", response);
      return response;
    })
    .catch((err) => {
      console.error("Foxhole native messaging error:", err);
      throw err;
    });
});
