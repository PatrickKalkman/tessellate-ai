'use client'

import { useEffect, useState } from 'react'

export function useImage(url: string): [HTMLImageElement | undefined, 'loading' | 'loaded' | 'failed'] {
  const [state, setState] = useState<[HTMLImageElement | undefined, 'loading' | 'loaded' | 'failed']>([
    undefined,
    'loading',
  ])

  useEffect(() => {
    if (!url) return

    const img = new window.Image()
    
    function onload() {
      setState([img, 'loaded'])
    }
    
    function onerror() {
      setState([undefined, 'failed'])
    }
    
    img.addEventListener('load', onload)
    img.addEventListener('error', onerror)
    img.crossOrigin = 'anonymous'
    img.src = url
    
    return () => {
      img.removeEventListener('load', onload)
      img.removeEventListener('error', onerror)
    }
  }, [url])

  return state
}