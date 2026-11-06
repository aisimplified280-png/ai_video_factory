// pipeline/contact-sheet.mjs
// Build a deterministic grid for every scene/motion frame; never silently drop scenes.

export function buildContactSheetFilter(inputCount, options = {}) {
  const count = Number(inputCount);
  const columns = Number(options.columns ?? 3);
  const cellWidth = Number(options.cellWidth ?? 360);
  const cellHeight = Number(options.cellHeight ?? 640);

  if (!Number.isInteger(count) || count < 1) {
    throw new Error("Contact sheet inputCount must be a positive integer.");
  }
  if (!Number.isInteger(columns) || columns < 1) {
    throw new Error("Contact sheet columns must be a positive integer.");
  }
  if (!Number.isInteger(cellWidth) || cellWidth < 16 || !Number.isInteger(cellHeight) || cellHeight < 16) {
    throw new Error("Contact sheet cell dimensions must be integers >= 16.");
  }

  const rows = Math.ceil(count / columns);
  const outputWidth = columns * cellWidth;
  const outputHeight = rows * cellHeight;
  const filters = [];

  for (let index = 0; index < count; index += 1) {
    filters.push(
      `[${index}:v]scale=${cellWidth}:${cellHeight}:flags=lanczos,setsar=1[v${index}]`
    );
  }

  const rowLabels = [];
  for (let row = 0; row < rows; row += 1) {
    const first = row * columns;
    const rowCount = Math.min(columns, count - first);
    const inputs = Array.from({ length: rowCount }, (_, offset) => `[v${first + offset}]`).join("");
    const rowLabel = `r${row}`;
    const needsPad = rowCount < columns;
    const pad = needsPad ? `,pad=${outputWidth}:${cellHeight}:0:0:black` : "";
    filters.push(`${inputs}hstack=inputs=${rowCount}${pad}[${rowLabel}]`);
    rowLabels.push(`[${rowLabel}]`);
  }

  filters.push(
    `${rowLabels.join("")}vstack=inputs=${rows},format=yuv420p[out]`
  );

  return {
    columns,
    rows,
    inputCount: count,
    outputWidth,
    outputHeight,
    filterComplex: filters.join(";"),
  };
}
