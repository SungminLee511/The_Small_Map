import { apiClient } from './client'
import type { POIDetail, POIType, LatLng } from '@/types/poi'

export interface SubmitPOIBody {
  poi_type: POIType
  location: LatLng
  name: string | null
  attributes: Record<string, unknown>
  submitted_gps: { lat: number; lng: number; accuracy_m: number }
  photo_upload_id?: string | null
}

export interface PresignedPhoto {
  upload_id: string
  upload_url: string
  fields: Record<string, string>
  expires_at: string
}

export interface SubmitDuplicate {
  duplicate: true
  existing_poi_id: string
  distance_m: number
}

export interface SubmitResult {
  status: 'created' | 'duplicate'
  detail?: POIDetail
  duplicate?: SubmitDuplicate
}

export async function presignPhoto(
  contentType: 'image/jpeg' | 'image/png' | 'image/webp',
): Promise<PresignedPhoto> {
  const { data } = await apiClient.post<PresignedPhoto>(
    '/uploads/photo-presign',
    { content_type: contentType },
  )
  return data
}

export async function uploadPhotoBytes(
  presigned: PresignedPhoto,
  file: Blob,
): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': presigned.fields['Content-Type'] ?? file.type,
  }
  // Use plain fetch to bypass the apiClient interceptors and base URL —
  // the presigned URL already encodes the bucket host.
  const resp = await fetch(presigned.upload_url, {
    method: 'PUT',
    body: file,
    headers,
  })
  if (!resp.ok) {
    throw new Error(`Photo upload failed: ${resp.status}`)
  }
}

export async function submitPOI(body: SubmitPOIBody): Promise<SubmitResult> {
  try {
    const { data } = await apiClient.post<POIDetail>('/pois', body)
    return { status: 'created', detail: data }
  } catch (err) {
    const e = err as {
      response?: { status?: number; data?: { detail?: SubmitDuplicate } }
    }
    if (e?.response?.status === 409 && e.response.data?.detail?.duplicate) {
      return { status: 'duplicate', duplicate: e.response.data.detail }
    }
    throw err
  }
}
