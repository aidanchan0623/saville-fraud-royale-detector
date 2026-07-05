export function normalizePlayerTagInput(value: string) {
  const cleaned = value.trim().toUpperCase().replace(/^%23/, "#");
  if (!cleaned) return "";
  return cleaned.startsWith("#") ? cleaned : `#${cleaned}`;
}

export function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "Not available";
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatConfidence(value: string | undefined) {
  if (!value) return "Low";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .replace(/[^A-Z]/gi, "")
    .slice(0, 3)
    .toUpperCase();
}
