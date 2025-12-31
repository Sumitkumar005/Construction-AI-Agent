import { useState } from 'react'
import { ChevronDown, ChevronUp, Home, Square, Layers } from 'lucide-react'

export default function FlooringBreakdown({ flooringData }) {
  const [expanded, setExpanded] = useState(true)
  
  if (!flooringData || !flooringData.total_sqft) {
    return null
  }

  const { total_sqft, by_room, by_type } = flooringData

  return (
    <div className="mt-6 border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center">
          <Layers className="h-5 w-5 text-primary-600 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">
            Detailed Flooring Breakdown
          </h3>
          <span className="ml-3 text-sm text-gray-500">
            ({total_sqft.toLocaleString()} sqft total)
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        )}
      </button>

      {expanded && (
        <div className="p-6 bg-white">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-sm text-blue-600 font-medium mb-1">Total Area</div>
              <div className="text-2xl font-bold text-blue-900">
                {total_sqft.toLocaleString()}
              </div>
              <div className="text-xs text-blue-600 mt-1">sqft</div>
            </div>
            {by_type?.hardwood_sqft > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="text-sm text-amber-600 font-medium mb-1">Hardwood</div>
                <div className="text-2xl font-bold text-amber-900">
                  {by_type.hardwood_sqft.toLocaleString()}
                </div>
                <div className="text-xs text-amber-600 mt-1">sqft</div>
              </div>
            )}
            {by_type?.tile_sqft > 0 && (
              <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
                <div className="text-sm text-teal-600 font-medium mb-1">Tile</div>
                <div className="text-2xl font-bold text-teal-900">
                  {by_type.tile_sqft.toLocaleString()}
                </div>
                <div className="text-xs text-teal-600 mt-1">sqft</div>
              </div>
            )}
            {by_type?.concrete_sqft > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="text-sm text-gray-600 font-medium mb-1">Concrete</div>
                <div className="text-2xl font-bold text-gray-900">
                  {by_type.concrete_sqft.toLocaleString()}
                </div>
                <div className="text-xs text-gray-600 mt-1">sqft</div>
              </div>
            )}
          </div>

          {/* Room-by-Room Breakdown */}
          <div className="mb-6">
            <div className="flex items-center mb-4">
              <Home className="h-5 w-5 text-primary-600 mr-2" />
              <h4 className="text-md font-semibold text-gray-900">Room-by-Room Breakdown</h4>
            </div>
            {by_room && Object.keys(by_room).length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Room
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Dimensions
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Area
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Flooring Type
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(by_room).map(([roomName, roomData]) => (
                      <tr key={roomName} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                          {roomName || 'Unnamed Room'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {roomData.length_ft && roomData.width_ft
                            ? `${roomData.length_ft}' × ${roomData.width_ft}'`
                            : 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {roomData.area_sqft?.toLocaleString()} sqft
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            roomData.flooring_type === 'hardwood'
                              ? 'bg-amber-100 text-amber-800'
                              : roomData.flooring_type === 'tile'
                              ? 'bg-teal-100 text-teal-800'
                              : roomData.flooring_type === 'concrete'
                              ? 'bg-gray-100 text-gray-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {roomData.flooring_type || 'Unknown'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Room-by-room breakdown is not available for this extraction. 
                  This may occur when dimensions are estimated from overall floor plan dimensions rather than individual room measurements.
                  The total area and type breakdown above are still accurate.
                </p>
              </div>
            )}
          </div>

          {/* Type-by-Type Breakdown */}
          {by_type && (
            <div>
              <div className="flex items-center mb-4">
                <Square className="h-5 w-5 text-primary-600 mr-2" />
                <h4 className="text-md font-semibold text-gray-900">Type-by-Type Breakdown</h4>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {by_type.hardwood_sqft > 0 && (
                  <div className="border border-gray-200 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Hardwood</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {by_type.hardwood_sqft.toLocaleString()} sqft
                    </div>
                  </div>
                )}
                {by_type.tile_sqft > 0 && (
                  <div className="border border-gray-200 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Tile</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {by_type.tile_sqft.toLocaleString()} sqft
                    </div>
                  </div>
                )}
                {by_type.carpet_sqft > 0 && (
                  <div className="border border-gray-200 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Carpet</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {by_type.carpet_sqft.toLocaleString()} sqft
                    </div>
                  </div>
                )}
                {by_type.concrete_sqft > 0 && (
                  <div className="border border-gray-200 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Concrete</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {by_type.concrete_sqft.toLocaleString()} sqft
                    </div>
                  </div>
                )}
                {by_type.underlayment_sqft > 0 && (
                  <div className="border border-gray-200 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Underlayment</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {by_type.underlayment_sqft.toLocaleString()} sqft
                    </div>
                  </div>
                )}
                {by_type.baseboard_linear_ft > 0 && (
                  <div className="border border-gray-200 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Baseboard</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {by_type.baseboard_linear_ft.toLocaleString()} linear ft
                    </div>
                  </div>
                )}
                {by_type.transition_strips > 0 && (
                  <div className="border border-gray-200 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Transition Strips</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {by_type.transition_strips} pieces
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

