import React from 'react'

function getNodeIcon(type) {
  switch (type) {
    case 'start': return '○'
    case 'end': return '◉'
    case 'approval': return '□'
    case 'condition': return '◇'
    default: return '·'
  }
}

function getNodeLabel(node) {
  let label = node.id
  if (node.assignee) label += ` (${node.assignee})`
  return label
}

function topologicalSort(nodes, edges) {
  const nodeMap = {}
  nodes.forEach(n => { nodeMap[n.id] = n })
  const inDegree = {}
  nodes.forEach(n => { inDegree[n.id] = 0 })
  edges.forEach(e => { inDegree[e.target] = (inDegree[e.target] || 0) + 1 })

  const queue = nodes.filter(n => inDegree[n.id] === 0).map(n => n.id)
  const sorted = []

  while (queue.length > 0) {
    const id = queue.shift()
    sorted.push(id)
    edges.filter(e => e.source === id).forEach(e => {
      inDegree[e.target]--
      if (inDegree[e.target] === 0) queue.push(e.target)
    })
  }

  // Add any remaining nodes not reached (disconnected)
  nodes.forEach(n => {
    if (!sorted.includes(n.id)) sorted.push(n.id)
  })

  return sorted.map(id => nodeMap[id])
}

export default function SimulationFlowChart({ definition, steps, visitedNodeIds, waitingNodeId }) {
  if (!definition) return null

  const { nodes, edges } = definition
  const sortedNodes = topologicalSort(nodes, edges)
  const visitedSet = new Set(visitedNodeIds || [])

  const lastStep = steps && steps.length > 0 ? steps[steps.length - 1] : null
  const currentNodeId = lastStep ? lastStep.node_id : null

  const conditionEdges = {}
  edges.forEach(e => {
    const sourceNode = nodes.find(n => n.id === e.source)
    if (sourceNode && sourceNode.type === 'condition') {
      if (!conditionEdges[e.source]) conditionEdges[e.source] = []
      conditionEdges[e.source].push(e)
    }
  })

  return (
    <div className="sim-flowchart">
      {sortedNodes.map((node, idx) => {
        const isVisited = visitedSet.has(node.id)
        const isCurrent = node.id === currentNodeId
        const isWaiting = node.id === waitingNodeId

        let nodeClass = 'sim-node'
        if (isCurrent || isWaiting) nodeClass += ' sim-node-current'
        else if (isVisited) nodeClass += ' sim-node-visited'
        else nodeClass += ' sim-node-unvisited'

        return (
          <div key={node.id}>
            <div className={nodeClass}>
              <span className="sim-node-icon">{getNodeIcon(node.type)}</span>
              <span className="sim-node-label">{getNodeLabel(node)}</span>
              <span className="sim-node-type">{node.type}</span>
            </div>

            {conditionEdges[node.id] && (
              <div className="sim-branches">
                {conditionEdges[node.id].map((edge, i) => (
                  <div key={i} className="sim-branch-edge">
                    <span className="sim-branch-arrow">→</span>
                    <span className="sim-branch-label">
                      {edge.condition || 'default'}
                    </span>
                    <span className="sim-branch-target">→ {edge.target}</span>
                  </div>
                ))}
              </div>
            )}

            {idx < sortedNodes.length - 1 && (
              <div className="sim-connector">│</div>
            )}
          </div>
        )
      })}
    </div>
  )
}
