export function getPressureRange(effectiveFormValues) {
  if (effectiveFormValues.risk === "conservative") {
    return "3% - 5%";
  }

  if (effectiveFormValues.risk === "balanced") {
    return "4% - 6%";
  }

  return "5% - 8%";
}

export function getVolumeRule(effectiveFormValues) {
  if (effectiveFormValues.style === "breakout") {
    return ">= 1.8";
  }

  if (effectiveFormValues.style === "trend_start") {
    return ">= 1.5";
  }

  return ">= 1.3";
}

export function getBaseDaysRule(effectiveFormValues) {
  if (effectiveFormValues.holding === "trend") {
    return "90 - 150 天";
  }

  if (effectiveFormValues.holding === "swing") {
    return "60 - 120 天";
  }

  return "35 - 80 天";
}

export function getValuationRule(effectiveFormValues) {
  if (effectiveFormValues.valuation === "high") {
    return "优先低于行业中位";
  }

  if (effectiveFormValues.valuation === "medium") {
    return "不过热即可";
  }

  return "仅作辅助条件";
}
