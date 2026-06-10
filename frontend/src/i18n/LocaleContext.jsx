import React, { createContext, useContext, useState } from 'react'
import { locales, defaultLocale } from './index'

const LocaleContext = createContext()

export function LocaleProvider({ children }) {
  const [locale, setLocaleState] = useState(
    () => localStorage.getItem('flowforge_locale') || defaultLocale
  )

  function setLocale(newLocale) {
    setLocaleState(newLocale)
    localStorage.setItem('flowforge_locale', newLocale)
  }

  function t(key) {
    return locales[locale]?.[key] || locales[defaultLocale]?.[key] || key
  }

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  )
}

export function useLocale() {
  return useContext(LocaleContext)
}
