import { Pressable, StyleSheet, Text, View } from "react-native"

import type { ChatAction, ChatSafety } from "../lib/chat-api"

type AnswerActionsProps = {
  actions: ChatAction[]
  safety?: ChatSafety
  notice: string | null
  onOpenUrl: (url: string) => void
  onScheduleReminder: (action: ChatAction) => void
}

function actionLabel(action: ChatAction): string {
  return action.type === "schedule_reminder" ? `Lembrar: ${action.label}` : action.label
}

export function AnswerActions({
  actions,
  safety,
  notice,
  onOpenUrl,
  onScheduleReminder,
}: AnswerActionsProps) {
  const triaged = safety?.triaged === true
  if (!triaged && actions.length === 0) {
    return null
  }

  function handlePress(action: ChatAction) {
    if (action.type === "schedule_reminder") {
      onScheduleReminder(action)
      return
    }
    if (action.url) {
      onOpenUrl(action.url)
    }
  }

  return (
    <View style={styles.container}>
      {triaged ? (
        <View style={styles.alert}>
          <Text style={styles.alertTitle}>Sinal de alerta</Text>
          <Text style={styles.alertText}>Procure atendimento agora. Não espere a resposta do chat.</Text>
        </View>
      ) : null}
      <View style={styles.row}>
        {actions.map((action) => (
          <Pressable
            accessibilityLabel={actionLabel(action)}
            accessibilityRole="button"
            key={`${action.type}-${action.label}`}
            onPress={() => handlePress(action)}
            style={[styles.chip, action.type === "call_emergency" && styles.emergencyChip]}
          >
            <Text
              style={[styles.chipText, action.type === "call_emergency" && styles.emergencyChipText]}
            >
              {actionLabel(action)}
            </Text>
          </Pressable>
        ))}
      </View>
      {notice ? <Text style={styles.notice}>{notice}</Text> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  container: { gap: 10, marginTop: 4 },
  alert: { borderRadius: 14, backgroundColor: "#FDECEC", padding: 12, gap: 4 },
  alertTitle: { color: "#8A1C1C", fontSize: 15, fontWeight: "700" },
  alertText: { color: "#8A1C1C", fontSize: 14, lineHeight: 20 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#C9CED6",
    backgroundColor: "#F2F4F7",
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipText: { fontSize: 14, fontWeight: "600", color: "#17191C" },
  emergencyChip: { backgroundColor: "#B42318", borderColor: "#B42318" },
  emergencyChipText: { color: "#FFFFFF" },
  notice: { fontSize: 13, lineHeight: 18, color: "#4A5160" },
})
