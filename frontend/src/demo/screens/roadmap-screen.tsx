import { useMemo, useState } from "react"
import { Pressable, StyleSheet, Text, View } from "react-native"

import { roadmapStatusLabels, RoadmapItem } from "../components/roadmap-item"
import { useDemoTheme } from "../components/demo-shell-theme"
import { getDemoFocusOutline } from "../components/demo-tokens"
import {
  ROADMAP_AREAS,
  ROADMAP_ITEMS,
  ROADMAP_SNAPSHOT,
  ROADMAP_STATUSES,
  filterRoadmapItems,
  getRoadmapCounts,
} from "../data/roadmap"
import type { RoadmapStatus } from "../types/roadmap"

const statusOrder: readonly RoadmapStatus[] = ROADMAP_STATUSES

export function RoadmapScreen() {
  const theme = useDemoTheme()
  const [status, setStatus] = useState<RoadmapStatus | "all">("all")
  const [area, setArea] = useState<string | "all">("all")
  const [focusedFilter, setFocusedFilter] = useState<string | null>(null)
  const visibleItems = useMemo(() => filterRoadmapItems(ROADMAP_ITEMS, { status, area }), [area, status])
  const catalogCounts = useMemo(() => getRoadmapCounts(ROADMAP_ITEMS), [])
  const visibleCounts = useMemo(() => getRoadmapCounts(visibleItems), [visibleItems])

  return (
    <View style={styles.screen}>
      <Text style={[styles.title, { color: theme.text }]}>O que ainda falta</Text>
      <Text style={{ color: theme.textMuted }}>
        Uma fotografia rastreável separa o que já tem evidência do que ainda depende de validação.
      </Text>

      <View style={[styles.overview, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.eyebrow, { color: theme.action }]}>VISÃO GERAL</Text>
        <Text style={[styles.projectName, { color: theme.text }]}>RagTest</Text>
        <Text style={[styles.snapshotBadge, { color: theme.text }]}>Fotografia do projeto</Text>
        <View style={styles.snapshot}>
          <Text style={{ color: theme.textMuted }}>Branch: {ROADMAP_SNAPSHOT.branch}</Text>
          <Text style={{ color: theme.textMuted }}>Commit-base: {ROADMAP_SNAPSHOT.commit}</Text>
          <Text style={{ color: theme.textMuted }}>Versão do snapshot: {ROADMAP_SNAPSHOT.version}</Text>
          <Text style={{ color: theme.textMuted }}>Data: {ROADMAP_SNAPSHOT.date}</Text>
        </View>
      </View>

      <View style={styles.architectureRow}>
        <View style={[styles.architecture, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Arquitetura atual</Text>
          <Text style={{ color: theme.textMuted }}>
            Demo/Expo → FastAPI → RAG/retrieval/grounding → Qdrant + provider.
          </Text>
          <Text style={{ color: theme.textMuted }}>
            O cliente demonstrativo permanece separado do núcleo RAG.
          </Text>
        </View>
        <View style={[styles.architecture, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Visão planejada</Text>
          <Text style={{ color: theme.textMuted }}>
            Integração ao Se Cuida Mulher é um alvo documentado, não uma integração oficial pronta.
          </Text>
          <Text style={{ color: theme.textMuted }}>
            Identidade, política clínica e ações do aplicativo dependem do sistema integrador.
          </Text>
        </View>
      </View>

      <View style={styles.filters}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Filtrar itens</Text>
        <View style={styles.filterRow}>
          <FilterButton label="Todos" selected={status === "all" && area === "all"} onPress={() => { setStatus("all"); setArea("all") }} focused={focusedFilter === "all"} onFocus={() => setFocusedFilter("all")} onBlur={() => setFocusedFilter(null)} theme={theme} />
          {statusOrder.map((filterStatus) => {
            const label = roadmapStatusLabels[filterStatus].label
            return <FilterButton key={filterStatus} label={label} accessibilityLabel={`Status: ${label}`} selected={status === filterStatus} onPress={() => setStatus(filterStatus)} focused={focusedFilter === filterStatus} onFocus={() => setFocusedFilter(filterStatus)} onBlur={() => setFocusedFilter(null)} theme={theme} />
          })}
        </View>
        <View style={styles.filterRow}>
          <Text style={[styles.filterLabel, { color: theme.textMuted }]}>Áreas:</Text>
          {ROADMAP_AREAS.map((filterArea) => <FilterButton key={filterArea} label={filterArea} accessibilityLabel={`Área: ${filterArea}`} selected={area === filterArea} onPress={() => setArea(filterArea)} focused={focusedFilter === filterArea} onFocus={() => setFocusedFilter(filterArea)} onBlur={() => setFocusedFilter(null)} theme={theme} />)}
        </View>
      </View>

      <View style={styles.catalogSummary}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Catálogo evidence-based</Text>
        <Text style={{ color: theme.textMuted }}>{visibleItems.length} {visibleItems.length === 1 ? "item visível" : "itens visíveis"}</Text>
        <View style={styles.countRow}>
          <Text style={{ color: theme.textMuted }}>{visibleCounts.byStatus.implemented} implementados</Text>
          <Text style={{ color: theme.textMuted }}>{visibleCounts.byStatus.partial} parciais</Text>
          <Text style={{ color: theme.textMuted }}>{visibleCounts.byStatus.planned} planejados</Text>
          <Text style={{ color: theme.textMuted }}>{visibleCounts.byStatus.research} em estudo</Text>
        </View>
      </View>

      <View style={styles.areaGrid}>
        {ROADMAP_AREAS.map((catalogArea) => (
          <View key={catalogArea} style={[styles.areaCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.areaTitle, { color: theme.text }]}>{catalogArea}</Text>
            <Text style={{ color: theme.textMuted }}>{catalogCounts.byArea[catalogArea]} {catalogCounts.byArea[catalogArea] === 1 ? "item" : "itens"}</Text>
            <Pressable
              accessibilityLabel={`Ver detalhes: ${catalogArea}`}
              accessibilityRole="button"
              onPress={() => setArea(catalogArea)}
              style={[styles.areaButton, { borderColor: theme.border, backgroundColor: theme.surfaceMuted }]}
            >
              <Text style={{ color: theme.action }}>Ver detalhes</Text>
            </Pressable>
          </View>
        ))}
      </View>

      {visibleItems.length === 0 ? (
        <Text style={[styles.empty, { color: theme.textMuted }]}>Não há itens para este filtro.</Text>
      ) : (
        <View style={styles.items}>
          {visibleItems.map((item) => <RoadmapItem key={item.id} allItems={ROADMAP_ITEMS} item={item} />)}
        </View>
      )}
    </View>
  )
}

function FilterButton({ label, accessibilityLabel, selected, onPress, focused, onFocus, onBlur, theme }: { label: string; accessibilityLabel?: string; selected: boolean; onPress: () => void; focused: boolean; onFocus: () => void; onBlur: () => void; theme: ReturnType<typeof useDemoTheme> }) {
  return <Pressable accessibilityLabel={accessibilityLabel ?? label} accessibilityRole="button" accessibilityState={{ selected }} onBlur={onBlur} onFocus={onFocus} onPress={onPress} style={[styles.filterButton, { borderColor: selected ? theme.action : theme.border, backgroundColor: selected ? theme.surfaceMuted : theme.surface }, getDemoFocusOutline(theme, focused)]}><Text style={{ color: selected ? theme.action : theme.textMuted }}>{label}</Text></Pressable>
}

const styles = StyleSheet.create({
  screen: { gap: 12 },
  title: { fontSize: 24, fontWeight: "800" },
  overview: { borderWidth: 1, borderRadius: 14, padding: 16, gap: 8 },
  eyebrow: { fontSize: 12, fontWeight: "800", letterSpacing: 1.2 },
  projectName: { fontSize: 22, fontWeight: "800" },
  snapshotBadge: { fontWeight: "700" },
  snapshot: { gap: 3 },
  architectureRow: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  architecture: { flex: 1, minWidth: 280, borderWidth: 1, borderRadius: 14, padding: 15, gap: 8 },
  sectionTitle: { fontSize: 16, fontWeight: "800" },
  filters: { gap: 8 },
  filterRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 8 },
  filterLabel: { fontWeight: "700" },
  filterButton: { minHeight: 44, justifyContent: "center", borderWidth: 1, borderRadius: 9, paddingHorizontal: 11, paddingVertical: 8 },
  catalogSummary: { gap: 5 },
  countRow: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  areaGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  areaCard: { flexBasis: 220, flexGrow: 1, borderWidth: 1, borderRadius: 12, padding: 13, gap: 7, minWidth: 180 },
  areaTitle: { fontSize: 15, fontWeight: "700", lineHeight: 21 },
  areaButton: { alignSelf: "flex-start", minHeight: 40, justifyContent: "center", borderWidth: 1, borderRadius: 8, paddingHorizontal: 11 },
  items: { gap: 10 },
  empty: { paddingVertical: 12 },
})
