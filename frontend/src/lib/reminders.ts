import type { ChatAction } from "./chat-api"

export type Reminder = {
  id: string
  label: string
  serviceId: string | null
  dueDate: Date
}

export function addDays(base: Date, days: number): Date {
  const result = new Date(base.getFullYear(), base.getMonth(), base.getDate())
  result.setDate(result.getDate() + days)
  return result
}

export function formatDate(date: Date): string {
  const day = String(date.getDate()).padStart(2, "0")
  const month = String(date.getMonth() + 1).padStart(2, "0")
  return `${day}/${month}/${date.getFullYear()}`
}

export function reminderFromAction(action: ChatAction, now: Date): Reminder | null {
  if (action.type !== "schedule_reminder" || action.suggested_in_days === null) {
    return null
  }
  return {
    id: `${action.service_id ?? "geral"}-${action.suggested_in_days}`,
    label: action.label,
    serviceId: action.service_id,
    dueDate: addDays(now, action.suggested_in_days),
  }
}
