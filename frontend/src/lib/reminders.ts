import type { ChatAction } from "./chat-api"

export type Reminder = {
  id: string
  label: string
  serviceId: string | null
  dueDate: string
}

export function formatIsoDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-")
  return `${day}/${month}/${year}`
}

export function reminderFromAction(action: ChatAction): Reminder | null {
  if (action.type !== "schedule_reminder" || !action.due_date) {
    return null
  }
  return {
    id: `${action.service_id ?? "geral"}-${action.due_date}`,
    label: action.label,
    serviceId: action.service_id,
    dueDate: action.due_date,
  }
}
