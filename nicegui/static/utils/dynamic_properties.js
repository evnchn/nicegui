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
      let result = cspSafeEval("(" + value + ")");
      if (result === undefined) {
        result = cspSafeEval(value);
      }
      if (result === undefined) {
        // Evaluation failed — keep the original `:attr` key intact so the caller can see
        // the raw expression instead of overwriting with undefined.
        console.error(`Error while converting ${attr} attribute to dynamic property`);
      } else {
        obj[attr.slice(1)] = result;
        delete obj[attr];
      }
    } else {
      if (recursive) {
        convertDynamicProperties(value, true);
      }
    }
  }
}
