/**
 * Client-side image compression to ~1600px max dimension @ JPEG quality 80.
 * Uses canvas + drawImage. On any failure (e.g. unsupported in jsdom),
 * returns the original blob.
 */
export async function compressImage(
  file: File,
  { maxDim = 1600, quality = 0.8 }: { maxDim?: number; quality?: number } = {},
): Promise<Blob> {
  if (typeof document === 'undefined') return file
  const url = URL.createObjectURL(file)
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const i = new Image()
      i.onload = () => resolve(i)
      i.onerror = () => reject(new Error('image decode failed'))
      i.src = url
    })
    const w = img.naturalWidth
    const h = img.naturalHeight
    const scale = Math.min(1, maxDim / Math.max(w, h))
    const cw = Math.round(w * scale)
    const ch = Math.round(h * scale)

    const canvas = document.createElement('canvas')
    canvas.width = cw
    canvas.height = ch
    const ctx = canvas.getContext('2d')
    if (!ctx) return file
    ctx.drawImage(img, 0, 0, cw, ch)
    return await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (!blob) return reject(new Error('toBlob failed'))
          resolve(blob)
        },
        'image/jpeg',
        quality,
      )
    })
  } finally {
    URL.revokeObjectURL(url)
  }
}
