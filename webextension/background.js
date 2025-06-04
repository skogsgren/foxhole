browser.tabs.onUpdated.addListener((tabId, { status }, tab) => {
  if (status !== "complete") return;
  browser.tabs
    .executeScript(tabId, {
      code: `
        browser.runtime.sendMessage({
          title: document.title,
          text: document.body.innerText,
          url: window.location.href
        });
      `,
    })
    .catch(() => {});
});

