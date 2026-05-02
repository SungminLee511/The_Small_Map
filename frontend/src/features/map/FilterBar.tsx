import { ALL_POI_TYPES, POI_TYPE_LABELS } from '@/types/poi'
import { POI_TYPE_LUCIDE } from './TypeIcon'
import type { POIType } from '@/types/poi'

interface FilterBarProps {
  activeTypes: POIType[]
  onChange: (types: POIType[]) => void
}

/**
 * Persistent filter bar: pinned at top, has explicit 전체/없음 quick toggles
 * and one rounded-pill button per POI type. Filter state is driven by the
 * parent (MapView wires it to ``?types=...`` via useTypesUrlParam).
 */
export function FilterBar({ activeTypes, onChange }: FilterBarProps) {
  const toggle = (t: POIType) => {
    if (activeTypes.includes(t)) {
      onChange(activeTypes.filter((x) => x !== t))
    } else {
      onChange([...activeTypes, t])
    }
  }

  const allSelected = activeTypes.length === ALL_POI_TYPES.length
  const noneSelected = activeTypes.length === 0
  const selectAll = () => onChange([...ALL_POI_TYPES])
  const selectNone = () => onChange([])

  return (
    <div className="absolute top-4 left-4 right-4 z-10 flex flex-wrap items-center gap-2 bg-white/90 backdrop-blur rounded-lg p-2 shadow-md">
      <div className="flex items-center gap-1 pr-2 mr-1 border-r border-gray-200">
        <button
          type="button"
          onClick={selectAll}
          disabled={allSelected}
          aria-pressed={allSelected}
          className={`px-2.5 py-1 rounded-full text-xs font-semibold transition ${
            allSelected
              ? 'bg-blue-500 text-white cursor-default'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          전체
        </button>
        <button
          type="button"
          onClick={selectNone}
          disabled={noneSelected}
          aria-pressed={noneSelected}
          className={`px-2.5 py-1 rounded-full text-xs font-semibold transition ${
            noneSelected
              ? 'bg-gray-700 text-white cursor-default'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          없음
        </button>
      </div>
      {ALL_POI_TYPES.map((t) => {
        const Icon = POI_TYPE_LUCIDE[t]
        const isActive = activeTypes.includes(t)
        return (
          <button
            key={t}
            type="button"
            onClick={() => toggle(t)}
            aria-pressed={isActive}
            data-testid={`filter-${t}`}
            className={`px-3 py-1 rounded-full text-sm font-medium transition inline-flex items-center gap-1.5 ${
              isActive ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
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
