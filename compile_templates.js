#!/usr/bin/env node
/**
 * Pre-compiles Vue template strings in NiceGUI component .js files
 * into render functions, so the Vue runtime-only build can be used
 * (eliminating the need for 'unsafe-eval' in CSP).
 */
const { compile } = require("@vue/compiler-dom");
const fs = require("fs");
const path = require("path");

const ELEMENTS_DIR = path.join(__dirname, "nicegui", "elements");
const FUNCTIONS_DIR = path.join(__dirname, "nicegui", "functions");

function extractTemplate(source) {
  const backtickMatch = source.match(/template\s*:\s*`([\s\S]*?)`/);
  if (backtickMatch) {
    return { template: backtickMatch[1], fullMatch: backtickMatch[0] };
  }
  const singleQuoteMatch = source.match(/template\s*:\s*'([^']*)'/);
  if (singleQuoteMatch) {
    return { template: singleQuoteMatch[1], fullMatch: singleQuoteMatch[0] };
  }
  const doubleQuoteMatch = source.match(/template\s*:\s*"([^"]*)"/);
  if (doubleQuoteMatch) {
    return { template: doubleQuoteMatch[1], fullMatch: doubleQuoteMatch[0] };
  }
  return null;
}

function compileComponent(filePath) {
  const source = fs.readFileSync(filePath, "utf-8");
  const extracted = extractTemplate(source);

  if (!extracted) {
    console.log(`  SKIP (no template): ${filePath}`);
    return false;
  }

  const templateStr = extracted.template.trim();
  console.log(`  Compiling: ${filePath}`);

  const result = compile(templateStr, {
    mode: "module",
    hoistStatic: true,
    cacheHandlers: true,
  });

  if (result.errors && result.errors.length > 0) {
    console.error(`  ERRORS in ${path.basename(filePath)}:`);
    result.errors.forEach((e) => console.error(`    ${e.message}`));
    process.exit(1);
  }

  const lines = result.code.split("\n");

  // Extract vue import line
  const vueImportLine = lines.find((l) => l.startsWith("import {") && l.includes('"vue"'));

  // Find the render function start
  const renderStartIdx = lines.findIndex((l) => l.startsWith("export function render"));

  // Extract hoisted constants (between imports and render function)
  const hoistedLines = [];
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i].trim();
    if (l.startsWith("import ")) continue;
    if (l === "") continue;
    if (i >= renderStartIdx) break;
    hoistedLines.push(lines[i]);
  }

  // Build the render function body (remove 'export ' prefix)
  const renderLines = lines.slice(renderStartIdx);
  const renderFn = renderLines.join("\n").replace("export function render", "render");

  // Replace template property with render function in the source
  let newSource = source.replace(extracted.fullMatch, renderFn);

  // Add hoisted constants before `export default`
  if (hoistedLines.length > 0) {
    const exportIdx = newSource.indexOf("export default");
    if (exportIdx >= 0) {
      newSource = newSource.slice(0, exportIdx) + hoistedLines.join("\n") + "\n\n" + newSource.slice(exportIdx);
    }
  }

  // Add vue imports at the top of the file
  if (vueImportLine) {
    const existingVueImport = newSource.match(/import\s*\{([^}]+)\}\s*from\s*["']vue["']/);
    if (existingVueImport) {
      const existingNames = existingVueImport[1].split(",").map((s) => s.trim());
      const newImportMatch = vueImportLine.match(/import\s*\{([^}]+)\}\s*from\s*["']vue["']/);
      const newNames = newImportMatch[1].split(",").map((s) => s.trim());
      const allNames = [...new Set([...existingNames, ...newNames])];
      newSource = newSource.replace(existingVueImport[0], `import { ${allNames.join(", ")} } from "vue"`);
    } else {
      const firstImportIdx = newSource.indexOf("import ");
      if (firstImportIdx >= 0) {
        newSource = newSource.slice(0, firstImportIdx) + vueImportLine + "\n" + newSource.slice(firstImportIdx);
      } else {
        newSource = vueImportLine + "\n\n" + newSource;
      }
    }
  }

  fs.writeFileSync(filePath, newSource);
  return true;
}

console.log("Pre-compiling Vue component templates...\n");

let compiled = 0;
let skipped = 0;

const dirs = [ELEMENTS_DIR, FUNCTIONS_DIR];

function findJsFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "dist" || entry.name === "lib" || entry.name === "node_modules") continue;
      results.push(...findJsFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith(".js")) {
      results.push(fullPath);
    }
  }
  return results;
}

for (const dir of dirs) {
  console.log(`Processing ${path.relative(__dirname, dir)}/`);

  for (const filePath of findJsFiles(dir)) {
    const relPath = path.relative(dir, filePath);
    if (compileComponent(filePath)) {
      compiled++;
    } else {
      skipped++;
    }
  }
}

console.log(`\nDone: ${compiled} compiled, ${skipped} skipped`);
