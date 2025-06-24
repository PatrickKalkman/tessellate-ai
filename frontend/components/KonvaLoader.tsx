'use client'

import { useEffect, useState } from 'react'

export function useImage(url: string): [HTMLImageElement | undefined, 'loaded' | 'loading' | 'failed'] {
  const [image, setImage] = useState<HTMLImageElement | undefined>()
  const [status, setStatus] = useState<'loaded' | 'loading' | 'failed'>('loading')

  useEffect(() => {
    if (!url) return

    const img = new Image()
    img.src = url
    
    img.onload = () => {
      setImage(img)
      setStatus('loaded')
      console.log(`Image loaded successfully: ${url}`)
    }
    
    img.onerror = (e) => {
      setStatus('failed')
      console.error(`Failed to load image: ${url}`, e)
    }

    return () => {
      img.onload = null
      img.onerror = null
    }
  }, [url])

  return [image, status]
}