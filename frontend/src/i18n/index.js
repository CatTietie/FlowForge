import zh from './locales/zh.js'
import en from './locales/en.js'

export const SUPPORTED_LOCALES = [
  { code: 'zh', label: '中文' },
  { code: 'en', label: 'English' },
]

export const locales = { zh, en }
export const defaultLocale = 'zh'
