export function convertDynamicProperties(obj, recursive) {
  if (typeof obj !== "object" || obj === null) {
    return;
  }
  if (Array.isArray(obj)) {
    if (recursive) {
      obj.forEach((v) => convertDynamicProperties(v, true));
    }
    return;
  }
  for (const [attr, value] of Object.entries(obj)) {
    if (attr.startsWith(":")) {
      // cspSafeEval returns undefined on parse errors (it uses script injection, not eval,
      // so errors don't throw). Try expression form first, then statement form as fallback.
      let result = cspSafeEval("(" + value + ")");
      if (result === undefined) {
        result = cspSafeEval(value);
      }
      if (result === undefined) {
        console.error(`Error while converting ${attr} attribute to dynamic property`);
      }
      obj[attr.slice(1)] = result;
      delete obj[attr];
    } else {
      if (recursive) {
        convertDynamicProperties(value, true);
      }
    }
  }
}
