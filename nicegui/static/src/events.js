export function stringifyEventArgs(args, event_args) {
  const result = [];
  args.forEach((arg, i) => {
    if (event_args !== null && i >= event_args.length) return;
    let filtered = {};
    if (typeof arg !== "object" || arg === null || Array.isArray(arg)) {
      filtered = arg;
    } else {
      for (let k in arg) {
        // ignore "Restricted" fields in Firefox (see #2469)
        if (k == "originalTarget") {
          try {
            arg[k].toString();
          } catch (e) {
            continue;
          }
        }
        if (event_args === null || event_args[i] === null || event_args[i].includes(k)) {
          filtered[k] = arg[k];
        }
      }
    }
    result.push(JSON.stringify(filtered, (k, v) => (v instanceof Node || v instanceof Window ? undefined : v)));
  });
  return result;
}

const waitingCallbacks = new Map();

export function throttle(callback, time, leading, trailing, id) {
  if (time <= 0) {
    // execute callback immediately and return
    callback();
    return;
  }
  if (waitingCallbacks.has(id)) {
    if (trailing) {
      // update trailing callback
      waitingCallbacks.set(id, callback);
    }
  } else {
    if (leading) {
      // execute leading callback and set timeout to block more leading callbacks
      callback();
      waitingCallbacks.set(id, null);
    } else if (trailing) {
      // set trailing callback and set timeout to execute it
      waitingCallbacks.set(id, callback);
    }
    if (leading || trailing) {
      // set timeout to remove block and to execute trailing callback
      setTimeout(() => {
        const trailingCallback = waitingCallbacks.get(id);
        if (trailingCallback) trailingCallback();
        waitingCallbacks.delete(id);
      }, 1000 * time);
    }
  }
}
