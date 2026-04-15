#!/usr/bin/env node
/**
 * Pre-compiles Vue template strings in NiceGUI component .js source files
 * into render functions, writing the compiled output to sibling .compiled.js files.
 * This allows the Vue runtime-only build to be used (eliminating the
 * need for 'unsafe-eval' in CSP).
 *
 * Usage:
 *   node compile_templates.js          # Compile X.js -> X.compiled.js
 *   node compile_templates.js --check  # Verify X.compiled.js files are up-to-date
 */
const { compile } = require("@vue/compiler-dom");
const fs = require("fs");
const path = require("path");

const CHECK_MODE = process.argv.includes("--check");
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

function compileComponent(srcPath) {
  const source = fs.readFileSync(srcPath, "utf-8");
  const extracted = extractTemplate(source);

  if (!extracted) {
    console.log(`  SKIP (no template): ${srcPath}`);
    return null;
  }

  const outputPath = srcPath.replace(/\.js$/, ".compiled.js");
  const srcBasename = path.basename(srcPath);
  const templateStr = extracted.template.trim();
  console.log(`  Compiling: ${srcPath}`);

  const warnings = [];
  const result = compile(templateStr, {
    mode: "module",
    hoistStatic: true,
    cacheHandlers: true,
    onError: (e) => warnings.push(e),
  });

  const fatalErrors = warnings.filter((e) => e.code !== 2);
  if (fatalErrors.length > 0) {
    console.error(`  ERRORS in ${srcBasename}:`);
    fatalErrors.forEach((e) => console.error(`    ${e.message}`));
    process.exit(1);
  }

  const lines = result.code.split("\n");

  const vueImportLine = lines.find((l) => l.startsWith("import {") && l.includes('"vue"'));
  const renderStartIdx = lines.findIndex((l) => l.startsWith("export function render"));

  const hoistedLines = [];
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i].trim();
    if (l.startsWith("import ")) continue;
    if (l === "") continue;
    if (i >= renderStartIdx) break;
    hoistedLines.push(lines[i]);
  }

  const renderLines = lines.slice(renderStartIdx);
  const renderFn = renderLines.join("\n").replace("export function render", "render");

  let newSource = source.replace(extracted.fullMatch, renderFn);

  if (hoistedLines.length > 0) {
    const exportIdx = newSource.indexOf("export default");
    if (exportIdx >= 0) {
      newSource = newSource.slice(0, exportIdx) + hoistedLines.join("\n") + "\n\n" + newSource.slice(exportIdx);
    }
  }

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

  const header = `// AUTO-GENERATED from ${srcBasename} \u2014 DO NOT EDIT\n`;
  newSource = header + newSource;

  return { outputPath, content: newSource };
}

console.log(CHECK_MODE ? "Checking compiled Vue templates...\n" : "Pre-compiling Vue component templates...\n");

let compiled = 0;
let skipped = 0;
let outOfDate = 0;

const dirs = [ELEMENTS_DIR, FUNCTIONS_DIR];

function findSrcJsFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "dist" || entry.name === "lib" || entry.name === "node_modules") continue;
      results.push(...findSrcJsFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith(".js") && !entry.name.endsWith(".compiled.js")) {
      results.push(fullPath);
    }
  }
  return results;
}

for (const dir of dirs) {
  console.log(`Processing ${path.relative(__dirname, dir)}/`);

  for (const srcPath of findSrcJsFiles(dir)) {
    const result = compileComponent(srcPath);
    if (result) {
      if (CHECK_MODE) {
        const existing = fs.existsSync(result.outputPath) ? fs.readFileSync(result.outputPath, "utf-8") : "";
        if (existing !== result.content) {
          console.error(`  OUT OF DATE: ${result.outputPath}`);
          outOfDate++;
        }
      } else {
        fs.writeFileSync(result.outputPath, result.content);
      }
      compiled++;
    } else {
      skipped++;
    }
  }
}

if (CHECK_MODE) {
  if (outOfDate > 0) {
    console.error(`\nFAILED: ${outOfDate} file(s) out of date. Run 'node compile_templates.js' to update.`);
    process.exit(1);
  }
  console.log(`\nOK: ${compiled} compiled files are up-to-date, ${skipped} skipped`);
} else {
  console.log(`\nDone: ${compiled} compiled, ${skipped} skipped`);
}
