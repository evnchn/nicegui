// Browser API polyfills for Vue/Quasar SSR in V8 (MiniRacer)
var noop = function() {};
var noopObj = function() { return {}; };

globalThis.window = globalThis;
globalThis.self = globalThis;
globalThis.document = {
  body: { classList: { add: noop, remove: noop, contains: function() { return false; } }, style: {}, appendChild: noop, offsetWidth: 1920, offsetHeight: 1080, clientWidth: 1920, clientHeight: 1080, scrollWidth: 1920, scrollHeight: 1080, getBoundingClientRect: function() { return { top: 0, left: 0, right: 1920, bottom: 1080, width: 1920, height: 1080, x: 0, y: 0 }; } },
  head: { appendChild: noop },
  documentElement: { style: {}, classList: { add: noop, remove: noop }, setAttribute: noop, getAttribute: function() { return null; }, offsetWidth: 1920, offsetHeight: 1080, clientWidth: 1920, clientHeight: 1080, scrollWidth: 1920, scrollHeight: 1080, getBoundingClientRect: function() { return { top: 0, left: 0, right: 1920, bottom: 1080, width: 1920, height: 1080, x: 0, y: 0 }; } },
  createElement: function(tag) {
    var el = {
      tagName: (tag || 'div').toUpperCase(), nodeType: 1, style: {},
      classList: { add: noop, remove: noop, contains: function() { return false; }, toggle: noop },
      setAttribute: noop, getAttribute: function() { return null; }, hasAttribute: function() { return false; }, removeAttribute: noop,
      appendChild: function(c) { return c; }, addEventListener: noop, removeEventListener: noop,
      insertBefore: function(c) { return c; }, removeChild: function(c) { return c; }, replaceChild: noop,
      remove: noop, cloneNode: function() { return globalThis.document.createElement(tag); },
      contains: function() { return false; },
      childNodes: [], children: [], firstChild: null, lastChild: null, parentNode: null, parentElement: null,
      nextSibling: null, previousSibling: null, nextElementSibling: null,
      innerHTML: '', outerHTML: '', textContent: '',
      dataset: {}, offsetWidth: 0, offsetHeight: 0, clientWidth: 0, clientHeight: 0,
      scrollWidth: 0, scrollHeight: 0, scrollTop: 0, scrollLeft: 0,
      getBoundingClientRect: function() { return { top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0, x: 0, y: 0 }; },
      querySelector: function() { return null; }, querySelectorAll: function() { return []; },
      getElementsByClassName: function() { return []; }, getElementsByTagName: function() { return []; },
      matches: function() { return false; }, closest: function() { return null; },
      focus: noop, blur: noop, click: noop,
      dispatchEvent: function() { return true; },
    };
    return el;
  },
  createTextNode: function() { return { textContent: '' }; },
  createComment: function() { return { textContent: '' }; },
  createDocumentFragment: function() { return { appendChild: noop, childNodes: [] }; },
  querySelector: function() { return null; },
  querySelectorAll: function() { return []; },
  getElementById: function() { return null; },
  getElementsByClassName: function() { return []; },
  getElementsByTagName: function() { return []; },
  location: { href: 'https://localhost/', protocol: 'https:', host: 'localhost', hostname: 'localhost', pathname: '/', search: '', hash: '' },
  addEventListener: noop,
  removeEventListener: noop,
  createEvent: function() { return { initEvent: noop }; },
  createRange: function() { return { setStart: noop, setEnd: noop, commonAncestorContainer: {} }; },
  implementation: { createHTMLDocument: function() { return globalThis.document; } },
};
globalThis.navigator = { userAgent: 'SSR', language: 'en-US', platform: 'SSR', languages: ['en-US'] };
globalThis.location = { href: 'https://localhost/', protocol: 'https:', host: 'localhost', hostname: 'localhost', pathname: '/', search: '', hash: '', origin: 'https://localhost', port: '' };
globalThis.history = { pushState: noop, replaceState: noop, back: noop, forward: noop, go: noop, state: null };
globalThis.getComputedStyle = function() {
  return new Proxy({}, { get: function(target, prop) {
    if (prop === 'getPropertyValue') return function() { return ''; };
    if (prop === 'length') return 0;
    return '';
  }});
};
globalThis.matchMedia = function() { return { matches: false, addListener: noop, removeListener: noop, addEventListener: noop, removeEventListener: noop, media: '' }; };
globalThis.requestAnimationFrame = function(cb) { return setTimeout(cb, 0); };
globalThis.cancelAnimationFrame = function(id) { clearTimeout(id); };
globalThis.requestIdleCallback = function(cb) { return setTimeout(cb, 0); };
globalThis.cancelIdleCallback = function(id) { clearTimeout(id); };
globalThis.ResizeObserver = function() { this.observe = noop; this.unobserve = noop; this.disconnect = noop; };
globalThis.MutationObserver = function() { this.observe = noop; this.disconnect = noop; this.takeRecords = function() { return []; }; };
globalThis.IntersectionObserver = function() { this.observe = noop; this.unobserve = noop; this.disconnect = noop; };
globalThis.HTMLElement = function() {};
globalThis.SVGElement = function() {};
globalThis.Element = function() {};
globalThis.Node = function() {};
globalThis.Event = function(t) { this.type = t; this.preventDefault = noop; this.stopPropagation = noop; };
globalThis.CustomEvent = function(t, o) { this.type = t; this.detail = o && o.detail; this.preventDefault = noop; this.stopPropagation = noop; };
globalThis.CSS = { supports: function() { return false; }, escape: function(s) { return s; } };
globalThis.screen = { width: 1920, height: 1080, availWidth: 1920, availHeight: 1080, orientation: { type: 'landscape-primary' } };
globalThis.innerWidth = 1920;
globalThis.innerHeight = 1080;
globalThis.devicePixelRatio = 1;
globalThis.scrollX = 0;
globalThis.scrollY = 0;
globalThis.pageXOffset = 0;
globalThis.pageYOffset = 0;
globalThis.scroll = noop;
globalThis.scrollTo = noop;
globalThis.scrollBy = noop;
globalThis.addEventListener = noop;
globalThis.removeEventListener = noop;
globalThis.dispatchEvent = function() { return true; };
globalThis.btoa = function(s) { return s; };
globalThis.atob = function(s) { return s; };
globalThis.performance = { now: function() { return Date.now(); }, mark: noop, measure: noop };
globalThis.XMLHttpRequest = function() { this.open = noop; this.send = noop; this.setRequestHeader = noop; this.addEventListener = noop; };
globalThis.fetch = function() { return Promise.resolve({ ok: true, json: function() { return Promise.resolve({}); } }); };
globalThis.File = function() {};
globalThis.FileList = function() {};
globalThis.FileReader = function() { this.readAsDataURL = noop; this.readAsText = noop; this.addEventListener = noop; };
globalThis.Blob = function() {};
globalThis.FormData = function() { this.append = noop; this.get = function() { return null; }; this.getAll = function() { return []; }; };
globalThis.URL = { createObjectURL: function() { return ''; }, revokeObjectURL: noop };
globalThis.URLSearchParams = function() { this.get = function() { return null; }; this.toString = function() { return ''; }; };
globalThis.AbortController = function() { this.signal = {}; this.abort = noop; };
globalThis.DOMParser = function() { this.parseFromString = function() { return globalThis.document; }; };
globalThis.Image = function() {};
globalThis.Audio = function() {};
globalThis.Worker = function() { this.postMessage = noop; this.terminate = noop; this.addEventListener = noop; };
globalThis.MessageChannel = function() { this.port1 = { postMessage: noop, addEventListener: noop }; this.port2 = { postMessage: noop, addEventListener: noop }; };
globalThis.WebSocket = function() { this.send = noop; this.close = noop; this.addEventListener = noop; };
globalThis.localStorage = { getItem: function() { return null; }, setItem: noop, removeItem: noop, clear: noop };
globalThis.sessionStorage = { getItem: function() { return null; }, setItem: noop, removeItem: noop, clear: noop };
globalThis.crypto = { randomUUID: function() { return '00000000-0000-0000-0000-000000000000'; }, getRandomValues: function(a) { return a; } };
