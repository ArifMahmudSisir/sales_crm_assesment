export type Lead = {
  name?: string
  title?: string
  company?: string
  email?: string
  score?: number
  persona?: string
  priority?: 'High' | 'Medium' | 'Low' | string
  status?: string
  response_class?: string
}