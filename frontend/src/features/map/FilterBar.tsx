import { ALL_POI_TYPES, POI_TYPE_LABELS } from '@/types/poi'
import { POI_TYPE_LUCIDE } from './TypeIcon'
import type { POIType } from '@/types/poi'

interface FilterBarProps {
  activeTypes: POIType[]
  onChange: (types: POIType[]) => void
}

export function FilterBar({ activeTypes, onChange }: FilterBarProps) {
  const toggle = (t: POIType) => {
    if (activeTypes.includes(t)) {
      onChange(activeTypes.filter((x) => x !== t))
    } else {
      onChange([...activeTypes, t])
    }
  }

  const allSelected = activeTypes.length === ALL_POI_TYPES.length
  const toggleAll = () => {
    onChange(allSelected ? [] : [...ALL_POI_TYPES])
  }

  return (
    <div className="absolute top-4 left-4 right-4 z-10 flex flex-wrap gap-2 bg-white/90 backdrop-blur rounded-lg p-2 shadow-md">
      <button
        onClick={toggleAll}
        className={`px-3 py-1 rounded-full text-sm font-medium transition ${
          allSelected ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
        }`}
      >
        {allSelected ? '전체 해제' : '전체 선택'}
      </button>
      {ALL_POI_TYPES.map((t) => {
        const Icon = POI_TYPE_LUCIDE[t]
        return (
          <button
            key={t}
            onClick={() => toggle(t)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition inline-flex items-center gap-1.5 ${
              activeTypes.includes(t)
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            <Icon size={16} aria-hidden="true" />
            {POI_TYPE_LABELS[t]}
          </button>
        )
      })}
    </div>
  )
}
