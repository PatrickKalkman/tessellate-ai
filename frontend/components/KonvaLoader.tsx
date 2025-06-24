'use client'

import { useEffect, useState } from 'react'
import Script from 'next/script'

declare global {
  interface Window {
    Konva: any
    ReactKonva: any
  }
}

export function loadKonvaFromCDN(): Promise<{
  Stage: any
  Layer: any
  Image: any
  Rect: any
  Line: any
  Group: any
}> {
  return new Promise((resolve) => {
    if (window.Konva && window.ReactKonva) {
      resolve({
        Stage: window.ReactKonva.Stage,
        Layer: window.ReactKonva.Layer,
        Image: window.ReactKonva.Image,
        Rect: window.ReactKonva.Rect,
        Line: window.ReactKonva.Line,
        Group: window.ReactKonva.Group,
      })
    } else {
      const checkInterval = setInterval(() => {
        if (window.Konva && window.ReactKonva) {
          clearInterval(checkInterval)
          resolve({
            Stage: window.ReactKonva.Stage,
            Layer: window.ReactKonva.Layer,
            Image: window.ReactKonva.Image,
            Rect: window.ReactKonva.Rect,
            Line: window.ReactKonva.Line,
            Group: window.ReactKonva.Group,
          })
        }
      }, 100)
    }
  })
}

export function KonvaScripts() {
  return (
    <>
      <Script
        src="https://unpkg.com/konva@9.3.20/konva.min.js"
        strategy="afterInteractive"
      />
      <Script
        src="https://unpkg.com/react-konva@18.2.10/umd/react-konva.min.js"
        strategy="afterInteractive"
      />
    </>
  )
}

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