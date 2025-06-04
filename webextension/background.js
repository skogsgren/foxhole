browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    console.log("Tab updated, injecting script into:", tab.url);
    browser.tabs
      .executeScript(tabId, {
        code: `
        console.log("Foxhole content script executing on", window.location.href);
        browser.runtime.sendMessage({
          title: document.title,
          text: document.body.innerText,
          url: window.location.href
        });
      `,
      })
      .catch((err) => {
        console.error("Foxhole script injection failed:", err);
      });
  }
});

browser.runtime.onMessage.addListener((message, sender) => {
  console.log("Foxhole received message from content script:", message);
  browser.runtime
    .sendNativeMessage("foxhole_host", message)
    .then((response) => {
      console.log("Foxhole native message response:", response);
    })
    .catch((err) => {
      console.error("Foxhole native messaging error:", err);
    });
});
