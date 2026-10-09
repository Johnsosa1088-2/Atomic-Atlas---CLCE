# Save work still open in version 001

Keep the old workbench tab open. Its annotations are held in that tab's memory. Opening the new HTML cannot transfer them automatically.

The following optional console command bypasses the old export limit by downloading a compact checkpoint directly from that tab. It makes no network calls, does not remove annotations, and does not change the ledger. Use it only in your existing annotation workbench tab.

1. Press F12 and select Console.
2. Paste the exact code below and execute it. Browser paste protection may require you to type the command manually or use your browser's approved paste workflow.
3. A JSON file downloads. Open the new `workbench.html` and import that JSON. Confirm your marks are visible before closing the old tab.

```javascript
(() => {
  const assets = Object.create(null);
  const compact = state => ({...state, images: state.images.map(image => {
    if (image.data === null) return {...image};
    assets[image.sha256] = image.data;
    return {...image, data: {$asset: image.sha256}};
  })});
  const source = ledger.project;
  const project = {...source, state: compact(source.state),
    events: source.events.map(event => ({...event, state: compact(event.state)}))};
  const blob = new Blob([JSON.stringify({format: 'AURELIA-CHECKPOINT-TRANSPORT-002', assets, project})], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = 'aurelia-rescued-checkpoint.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
})();
```

If the console says `ledger is not defined`, stop: the console is in the wrong tab or frame, or the page is not the version 001 workbench. Do not close your current page until it has been saved.
