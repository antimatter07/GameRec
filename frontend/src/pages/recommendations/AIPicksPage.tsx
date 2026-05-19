import { useMemo } from 'react';
import { isAxiosError } from 'axios';
import {
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconArrowRight,
  IconBolt,
  IconBrain,
  IconCalendarTime,
  IconGauge,
  IconRefresh,
  IconSparkles,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { useAIPicks, useRefreshAIPicks } from '../../hooks/useRecommendations';
import type { RecommendationItem } from '../../types/recommendation';
import classes from './AIPicksPage.module.css';

const generatedAtFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
});

function formatGeneratedAt(isoString: string | null | undefined) {
  if (!isoString) return 'Waiting for first batch';
  return generatedAtFormatter.format(new Date(isoString));
}

function formatGameMeta(item: RecommendationItem) {
  const segments: string[] = [];
  const releaseYear = item.game.released ? new Date(item.game.released).getFullYear() : null;

  if (releaseYear) segments.push(String(releaseYear));
  if (item.game.genres.length > 0) segments.push(item.game.genres.slice(0, 2).map((genre) => genre.name).join(' / '));
  if (item.game.rating !== null) segments.push(`RAWG ${item.game.rating.toFixed(1)}`);
  if (item.game.hltb_main_hours !== null) segments.push(`${Math.round(item.game.hltb_main_hours)}h main`);

  return segments.length > 0 ? segments : ['Metadata still filling in'];
}

function summarizePickedGenres(items: RecommendationItem[]) {
  const counts = new Map<string, number>();

  items.forEach((item) => {
    item.game.genres.forEach((genre) => {
      counts.set(genre.name, (counts.get(genre.name) ?? 0) + 1);
    });
  });

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 5)
    .map(([name, count]) => ({ name, count }));
}

export default function AIPicksPage() {
  const { data, isLoading, isError } = useAIPicks();
  const refresh = useRefreshAIPicks();
  const navigate = useNavigate();

  const recommendation = data?.recommendation ?? null;
  const status = recommendation?.status ?? null;
  const items = recommendation?.items ?? [];
  const hasItems = items.length > 0;
  const readyRecommendation = status === 'ready' ? recommendation : null;

  const confidenceValues = useMemo(
    () => items.map((item) => item.confidence).filter((value): value is number => value !== null),
    [items],
  );
  const averageConfidence = confidenceValues.length > 0
    ? confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length
    : null;
  const strongMatchCount = confidenceValues.filter((value) => value >= 0.75).length;
  const pickedGenres = useMemo(() => summarizePickedGenres(items), [items]);

  const handleRefresh = async () => {
    try {
      await refresh.mutateAsync();
      notifications.show({
        color: 'teal',
        message: 'AI Picks refresh started. We will update this page automatically.',
      });
    } catch (error: unknown) {
      const detail = isAxiosError(error) ? (error.response?.data?.detail as string | undefined) : undefined;
      notifications.show({
        color: 'red',
        message: detail ?? 'Failed to refresh AI Picks.',
      });
    }
  };

  if (isLoading) {
    return (
      <Center py={80}>
        <Stack align="center" gap="sm">
          <Loader color="violet" size="md" />
          <Text size="sm" c="dimmed">Loading AI Picks…</Text>
        </Stack>
      </Center>
    );
  }

  if (isError) {
    return (
      <Center py={80}>
        <Paper p="md" radius="md" withBorder>
          <Group gap="sm" wrap="nowrap">
            <div className={classes.statusIcon} style={{ background: 'rgba(250, 82, 82, 0.12)' }}>
              <IconAlertCircle size={16} color="var(--mantine-color-red-5)" />
            </div>
            <Text size="sm" c="red.4">Failed to load AI Picks.</Text>
          </Group>
        </Paper>
      </Center>
    );
  }

  const statusTone = status === 'failed'
    ? {
        label: 'Generation issue',
        icon: <IconAlertCircle size={16} color="var(--mantine-color-red-5)" />,
        background: 'rgba(250, 82, 82, 0.12)',
      }
    : status === 'pending'
      ? {
          label: 'Generating batch',
          icon: <Loader size={16} color="var(--mantine-color-violet-5)" />,
          background: 'rgba(124, 92, 252, 0.14)',
        }
      : data?.is_stale
        ? {
            label: 'Cached batch',
            icon: <IconRefresh size={16} color="var(--mantine-color-yellow-5)" />,
            background: 'rgba(252, 196, 25, 0.12)',
          }
        : {
            label: 'Fresh batch',
            icon: <IconSparkles size={16} color="var(--mantine-color-teal-5)" />,
            background: 'rgba(18, 184, 134, 0.12)',
          };

  return (
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            AI <span className={classes.headerAccent}>Picks</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Grounded recommendations shaped by your library, ratings, and play history — in a tighter, easier-to-scan list.
          </Text>
        </div>

        <Button
          leftSection={<IconRefresh size={16} />}
          onClick={handleRefresh}
          loading={refresh.isPending}
          disabled={data ? !data.can_refresh : false}
          color="violet"
          variant={hasItems ? 'light' : 'filled'}
        >
          {hasItems ? 'Refresh AI Picks' : 'Generate AI Picks'}
        </Button>
      </div>

      <Paper p="md" radius="md" withBorder className={classes.statusPanel}>
        <Group justify="space-between" align="flex-start" gap="sm" className={classes.panelHeader}>
          <Group gap="sm" wrap="nowrap">
            <div className={classes.statusIcon} style={{ background: statusTone.background }}>
              {statusTone.icon}
            </div>
            <div>
              <Text size="sm" fw={600}>{statusTone.label}</Text>
              <Text size="xs" c="dimmed">
                {data?.detail ?? 'This batch updates automatically while generation is in progress.'}
              </Text>
            </div>
          </Group>

          <Badge size="sm" variant="light" color={data?.is_stale ? 'yellow' : 'violet'}>
            Cache {data?.cache_hours ?? 24}h
          </Badge>
        </Group>
      </Paper>

      {!recommendation && (
        <Paper p="md" radius="md" withBorder className={classes.emptyState}>
          <div>
            <Text size="sm" fw={600}>No AI Picks yet</Text>
            <Text size="xs" c="dimmed" mt={4}>
              Add a few games, ratings, or journal entries, then generate your first AI Picks batch.
            </Text>
          </div>
        </Paper>
      )}

      {readyRecommendation && hasItems && (
        <>
          <div className={classes.metricsGrid}>
            <Paper className={classes.metricCard} p="md" radius="md" withBorder>
              <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-violet-light)' }}>
                <IconSparkles size={18} color="var(--mantine-color-violet-5)" />
              </div>
              <div className={classes.metricLabel}>Picks in batch</div>
              <div className={classes.metricValue} style={{ color: 'var(--mantine-color-violet-4)' }}>
                {items.length}
              </div>
              <div className={classes.metricSub}>Current recommendation set</div>
            </Paper>

            <Paper className={classes.metricCard} p="md" radius="md" withBorder>
              <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-teal-light)' }}>
                <IconGauge size={18} color="var(--mantine-color-teal-5)" />
              </div>
              <div className={classes.metricLabel}>Avg confidence</div>
              <div className={classes.metricValue} style={{ color: 'var(--mantine-color-teal-4)' }}>
                {averageConfidence !== null ? `${Math.round(averageConfidence * 100)}%` : '—'}
              </div>
              <div className={classes.metricSub}>Across picks with confidence scores</div>
            </Paper>

            <Paper className={classes.metricCard} p="md" radius="md" withBorder>
              <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-blue-light)' }}>
                <IconBolt size={18} color="var(--mantine-color-blue-5)" />
              </div>
              <div className={classes.metricLabel}>Strong matches</div>
              <div className={classes.metricValue} style={{ color: 'var(--mantine-color-blue-4)' }}>
                {strongMatchCount}
              </div>
              <div className={classes.metricSub}>Confidence at 75% or higher</div>
            </Paper>

            <Paper className={classes.metricCard} p="md" radius="md" withBorder>
              <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-yellow-light)' }}>
                <IconCalendarTime size={18} color="var(--mantine-color-yellow-5)" />
              </div>
              <div className={`${classes.metricValue} ${classes.metricValueCompact}`} style={{ color: 'var(--mantine-color-yellow-4)' }}>
                {data?.cache_hours ?? 24}h
              </div>
              <div className={classes.metricLabel}>Refresh window</div>
              <div className={classes.metricSub}>Generated {formatGeneratedAt(readyRecommendation.generated_at)}</div>
            </Paper>
          </div>

          <div className={classes.overviewGrid}>
            <Paper p="md" radius="md" withBorder>
              <Group justify="space-between" mb="sm" className={classes.panelHeader}>
                <div>
                  <Text size="sm" fw={600}>Taste summary</Text>
                  <Text size="xs" c="dimmed">A concise read on what the current batch is optimizing for.</Text>
                </div>
                <Badge size="sm" variant="light" color="violet">
                  {readyRecommendation.model_name ?? 'AI'}
                </Badge>
              </Group>

              <Text size="sm" c="dimmed" className={classes.summaryText}>
                {readyRecommendation.summary ?? 'The model is still generating a summary for this batch.'}
              </Text>
            </Paper>

            <Paper p="md" radius="md" withBorder>
              <Group justify="space-between" mb="sm" className={classes.panelHeader}>
                <div>
                  <Text size="sm" fw={600}>Batch signals</Text>
                  <Text size="xs" c="dimmed">Patterns showing up across the recommendations.</Text>
                </div>
                <div className={classes.noteIcon}>
                  <IconBrain size={16} color="var(--mantine-color-violet-5)" />
                </div>
              </Group>

              {pickedGenres.length > 0 ? (
                <Stack gap="sm">
                  <div className={classes.genreCloud}>
                    {pickedGenres.map((genre, index) => (
                      <Badge key={genre.name} size="sm" variant="light" color={index === 0 ? 'violet' : 'gray'}>
                        {genre.name} {genre.count}
                      </Badge>
                    ))}
                  </div>
                  <Text size="xs" c="dimmed" className={classes.noteText}>
                    The current batch leans most heavily into {pickedGenres[0].name.toLowerCase()}-adjacent games.
                  </Text>
                </Stack>
              ) : (
                <Text size="sm" c="dimmed">
                  Recommendation signals will show up here once the batch fills in more metadata.
                </Text>
              )}
            </Paper>
          </div>

          <Paper p="md" radius="md" withBorder>
            <Group justify="space-between" align="flex-start" gap="sm" mb="md" className={classes.panelHeader}>
              <div>
                <Text size="sm" fw={600}>Current picks</Text>
                <Text size="xs" c="dimmed">Compact rows with confidence, rationale, and a quick route into each game.</Text>
              </div>
              <Text size="xs" c="dimmed" className={classes.panelMeta}>
                {items.length} recommendation{items.length === 1 ? '' : 's'}
              </Text>
            </Group>

            <Stack gap="xs">
              {items.map((item) => {
                const confidencePercent = item.confidence !== null ? Math.round(item.confidence * 100) : null;
                const metaSegments = formatGameMeta(item);

                return (
                  <div key={item.id} className={classes.pickRow}>
                    <div className={classes.pickRank}>#{item.rank}</div>

                    <div className={classes.pickCover}>
                      {item.game.background_image ? (
                        <img src={item.game.background_image} alt={item.game.name} />
                      ) : (
                        <Text size="lg">🎮</Text>
                      )}
                    </div>

                    <div className={classes.pickBody}>
                      <Group justify="space-between" align="flex-start" gap="sm" wrap="nowrap" className={classes.pickTop}>
                        <div className={classes.pickInfo}>
                          <div className={classes.pickTitle}>{item.game.name}</div>
                          <div className={classes.pickMeta}>
                            {metaSegments.map((segment, index) => (
                              <span key={`${item.id}-${index}`}>{segment}</span>
                            ))}
                          </div>
                        </div>

                        {confidencePercent !== null && (
                          <div className={classes.confidenceBlock}>
                            <div className={classes.confidenceLabel}>Confidence</div>
                            <div className={classes.confidenceValue}>{confidencePercent}%</div>
                          </div>
                        )}
                      </Group>

                      {confidencePercent !== null && (
                        <div className={classes.confidenceTrack}>
                          <div
                            className={classes.confidenceFill}
                            style={{ width: `${Math.max(confidencePercent, confidencePercent > 0 ? 10 : 0)}%` }}
                          />
                        </div>
                      )}

                      {item.explanation && (
                        <Text size="sm" className={classes.pickExplanation}>
                          {item.explanation}
                        </Text>
                      )}

                      <Group justify="space-between" align="center" gap="sm" className={classes.pickFooter}>
                        <Text size="xs" c="dimmed" className={classes.pickReason}>
                          {item.because_you_liked && item.because_you_liked.length > 0
                            ? `Because you liked ${item.because_you_liked.join(', ')}.`
                            : 'Picked from your current taste profile.'}
                        </Text>

                        <Button
                          size="xs"
                          variant="subtle"
                          color="violet"
                          rightSection={<IconArrowRight size={14} />}
                          onClick={() => navigate(`/games/${item.game.id}`)}
                        >
                          View game
                        </Button>
                      </Group>
                    </div>
                  </div>
                );
              })}
            </Stack>
          </Paper>
        </>
      )}
    </Stack>
  );
}
