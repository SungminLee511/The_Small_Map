import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchPOIs } from '@/api/pois'
import { apiClient } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

describe('fetchPOIs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sends correct bbox query param', async () => {
    const mockData = { items: [], truncated: false }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockData })

    const bbox = { west: 126.9, south: 37.54, east: 126.94, north: 37.56 }
    const result = await fetchPOIs(bbox)

    expect(apiClient.get).toHaveBeenCalledWith('/pois', {
      params: { bbox: '126.9,37.54,126.94,37.56' },
    })
    expect(result).toEqual(mockData)
  })

  it('sends type filter when provided', async () => {
    const mockData = { items: [], truncated: false }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockData })

    const bbox = { west: 126.9, south: 37.54, east: 126.94, north: 37.56 }
    await fetchPOIs(bbox, ['toilet', 'bench'])

    expect(apiClient.get).toHaveBeenCalledWith('/pois', {
      params: { bbox: '126.9,37.54,126.94,37.56', type: ['toilet', 'bench'] },
    })
  })

  it('returns items and truncated flag', async () => {
    const mockData = {
      items: [
        {
          id: '123',
          poi_type: 'toilet',
          location: { lat: 37.55, lng: 126.92 },
          name: 'Test',
          attributes: null,
          source: 'seed',
          status: 'active',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      truncated: false,
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockData })

    const bbox = { west: 126.9, south: 37.54, east: 126.94, north: 37.56 }
    const result = await fetchPOIs(bbox)

    expect(result.items).toHaveLength(1)
    expect(result.items[0].poi_type).toBe('toilet')
    expect(result.truncated).toBe(false)
  })
})
