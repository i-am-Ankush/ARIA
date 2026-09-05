/**
 * Utility to parse Prometheus text format output into structured JavaScript object
 * @param {string} rawText 
 * @returns {Object} parsed metrics object
 */
export function parsePrometheusMetrics(rawText) {
  if (!rawText) return {};

  const lines = rawText.split('\n');
  const metrics = {};
  let currentHelp = '';
  let currentType = '';

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith('# HELP')) {
      const parts = trimmed.split(' ');
      const metricName = parts[2];
      currentHelp = parts.slice(3).join(' ');
      if (!metrics[metricName]) metrics[metricName] = {};
      metrics[metricName].help = currentHelp;
    } else if (trimmed.startsWith('# TYPE')) {
      const parts = trimmed.split(' ');
      const metricName = parts[2];
      currentType = parts[3];
      if (!metrics[metricName]) metrics[metricName] = {};
      metrics[metricName].type = currentType;
    } else if (!trimmed.startsWith('#')) {
      // Metric line: e.g. aria_payments_total 500 or aria_recovery_rate_pct{label="val"} 61.8
      const spaceIdx = trimmed.lastIndexOf(' ');
      if (spaceIdx !== -1) {
        const metricKey = trimmed.substring(0, spaceIdx).trim();
        const valueStr = trimmed.substring(spaceIdx + 1).trim();
        const numVal = parseFloat(valueStr);

        // Handle possible label syntax like metric_name{foo="bar"}
        const labelStart = metricKey.indexOf('{');
        let baseName = metricKey;
        let labels = {};

        if (labelStart !== -1) {
          baseName = metricKey.substring(0, labelStart);
          const labelContent = metricKey.substring(labelStart + 1, metricKey.indexOf('}'));
          labelContent.split(',').forEach(kv => {
            const [k, v] = kv.split('=');
            if (k && v) labels[k.trim()] = v.replace(/"/g, '').trim();
          });
        }

        if (!metrics[baseName]) metrics[baseName] = {};
        metrics[baseName].value = isNaN(numVal) ? valueStr : numVal;
        if (Object.keys(labels).length > 0) {
          metrics[baseName].labels = labels;
        }
      }
    }
  }

  return metrics;
}
