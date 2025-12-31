export default function EmptyState({ 
  icon: Icon,
  title,
  description,
  action,
  className 
}) {
  return (
    <div className={`text-center py-12 px-4 ${className}`}>
      {Icon && (
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gray-100 mb-4">
          <Icon className="h-8 w-8 text-gray-400" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">{description}</p>
      )}
      {action && (
        <div>{action}</div>
      )}
    </div>
  )
}


