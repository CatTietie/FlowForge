export function resolveLocalized(baseValue, i18nMap, locale, fallbackLocale = 'zh') {
  if (!i18nMap) return baseValue
  return i18nMap[locale] || i18nMap[fallbackLocale] || baseValue
}

export function resolveOptions(options, optionsI18n, locale, fallbackLocale = 'zh') {
  if (!optionsI18n) return options || []
  return optionsI18n[locale] || optionsI18n[fallbackLocale] || options || []
}

export function resolveNodeName(node, locale, fallbackLocale = 'zh') {
  if (node.name_i18n) {
    return node.name_i18n[locale] || node.name_i18n[fallbackLocale] || node.name || node.id
  }
  return node.name || node.id
}
