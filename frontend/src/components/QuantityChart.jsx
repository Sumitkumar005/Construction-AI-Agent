import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import FlooringBreakdown from './FlooringBreakdown'

export default function QuantityChart({ quantities }) {
  const data = Object.entries(quantities).map(([category, tradeData]) => {
    // Handle different trade types with different quantity fields
    let quantity = 0
    let unit = ''
    
    if (tradeData.total_sqft !== undefined) {
      // Flooring, painting, drywall (area-based)
      quantity = tradeData.total_sqft
      unit = 'sqft'
    } else if (tradeData.total_count !== undefined) {
      // Doors, windows (count-based)
      quantity = tradeData.total_count
      unit = 'count'
    } else if (typeof tradeData === 'number') {
      // Direct number
      quantity = tradeData
    } else if (tradeData.by_type) {
      // Try to sum by_type values for flooring
      const byType = tradeData.by_type || {}
      quantity = byType.hardwood_sqft || byType.tile_sqft || byType.carpet_sqft || tradeData.total_sqft || 0
      unit = 'sqft'
    } else {
      // Fallback: try to find any numeric value
      quantity = tradeData.total || tradeData.count || tradeData.quantity || 0
    }
    
    return {
      category: category.charAt(0).toUpperCase() + category.slice(1).replace(/_/g, ' '),
      quantity: quantity,
      unit: unit,
      rawData: tradeData // Keep for detailed view
    }
  })

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No quantity data available
      </div>
    )
  }

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="category" />
          <YAxis />
          <Tooltip 
            formatter={(value, name, props) => {
              const unit = props.payload?.unit
              return unit ? `${value.toLocaleString()} ${unit}` : value.toLocaleString()
            }}
          />
          <Legend />
          <Bar dataKey="quantity" fill="#0ea5e9" name="Quantity" />
        </BarChart>
      </ResponsiveContainer>

      {/* Summary Table */}
      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Quantity
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((item, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {item.category}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.quantity.toLocaleString()} {item.unit && <span className="text-gray-400">({item.unit})</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detailed Breakdowns for Each Trade */}
      {Object.entries(quantities).map(([category, tradeData]) => {
        if (category === 'flooring' && tradeData.total_sqft) {
          return <FlooringBreakdown key={category} flooringData={tradeData} />
        }
        return null
      })}
    </div>
  )
}

