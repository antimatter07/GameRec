import {
  ActionIcon,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
  Tooltip,
} from '@mantine/core';
import {
  IconAlertCircle,
  IconArrowRight,
  IconBrain,
  IconChecks,
  IconSparkles,
  IconThumbDown,
  IconThumbUp,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { useRecommendations, useSubmitFeedback } from '../../hooks/useRecommendations';
import { useAuthStore } from '../../store/authStore';
import type { RecommendationItem } from '../../types/recommendation';
import classes from './RecommendationsPage.module.css';

const generatedAtFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
});

function formatGeneratedAt(isoString: string | null | undefined) {
  if (!isoString) return 'Waiting for first run';
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

/**
 * Main recommendations page.
 * TODO: Add premium filter bar (genre, platform, release year) — show only for premium/admin
 * TODO: Add "Refresh Recommendations" button that invalidates the query
 * TODO: Add recommendation history link/tab
 * TODO: Show GameDNA link for premium users
 */
export default function RecommendationsPage() {
  const user = useAuthStore((s) => s.user);
  const isPremium = user?.role === 'premium' || user?.role === 'admin';
  const navigate = useNavigate();

  const { data, isLoading, isError } = useRecommendations();
  const { mutate: submitFeedback } = useSubmitFeedback();
  const items = data?.items ?? [];
  const averageMatch = items.length > 0
    ? items.reduce((sum, item) => sum + item.score, 0) / items.length
    : null;
  const strongMatchCount = items.filter((item) => item.score >= 0.75).length;

  if (isLoading) {
    return (
      <Center py={80}>
        <Stack align="center" gap="sm">
          <Loader color="ember" size="md" />
          <Text size="sm" c="dimmed">Loading recommendations…</Text>
        </Stack>
      </Center>
    );
  }

  if (isError) {
    return (
      <Center py={80}>
        <Paper p="md" radius="xs" withBorder>
          <Group gap="sm" wrap="nowrap">
            <div className={classes.statusIcon} style={{ background: 'rgba(250, 82, 82, 0.12)' }}>
              <IconAlertCircle size={16} color="var(--mantine-color-red-5)" />
            </div>
            <Text size="sm" c="red.4">Failed to load recommendations.</Text>
          </Group>
        </Paper>
      </Center>
    );
  }

  return (
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            Cosine <span className={classes.headerAccent}>Recommendations</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Content-based matches from your rated library profile, ranked by genre and tag similarity.
          </Text>
        </div>

        <Group gap="xs">
          {isPremium && (
            <Badge size="sm" variant="light" color="ember">
              Premium explanations
            </Badge>
          )}
          {/* TODO: Add "Refresh" button */}
          <Button size="xs" variant="light" color="ember" disabled>
            Refresh
          </Button>
        </Group>
      </div>

      <div className={classes.metricsGrid}>
        <Paper className={classes.metricCard} p="md" radius="xs" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-ember-light)' }}>
            <IconSparkles size={18} color="var(--mantine-color-ember-5)" />
          </div>
          <div className={classes.metricLabel}>Matches</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-ember-4)' }}>
            {items.length}
          </div>
          <div className={classes.metricSub}>Current ranked set</div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="xs" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-teal-light)' }}>
            <IconChecks size={18} color="var(--mantine-color-teal-5)" />
          </div>
          <div className={classes.metricLabel}>Avg match</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-teal-4)' }}>
            {averageMatch !== null ? `${Math.round(averageMatch * 100)}%` : '-'}
          </div>
          <div className={classes.metricSub}>Cosine similarity mean</div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="xs" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-blue-light)' }}>
            <IconBrain size={18} color="var(--mantine-color-blue-5)" />
          </div>
          <div className={classes.metricLabel}>Strong matches</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-blue-4)' }}>
            {strongMatchCount}
          </div>
          <div className={classes.metricSub}>Similarity at 75% or higher</div>
        </Paper>
      </div>

      {!data || items.length === 0 ? (
        <Paper p="md" radius="xs" withBorder className={classes.emptyState}>
          <div>
            <Text size="sm" fw={600}>No recommendations yet</Text>
            <Text size="xs" c="dimmed" mt={4}>
              Save wishlist ideas, add backlog games, and rate what you play to build a taste profile.
            </Text>
          </div>
        </Paper>
      ) : (
        <Paper p="md" radius="xs" withBorder>
          <Group justify="space-between" align="flex-start" gap="sm" mb="md" className={classes.panelHeader}>
            <div>
              <Text size="sm" fw={600}>Current matches</Text>
              <Text size="xs" c="dimmed">Compact game rows with similarity score and feedback.</Text>
            </div>
            <Text size="xs" c="dimmed" className={classes.panelMeta}>
              Generated {formatGeneratedAt(data.generated_at)}
            </Text>
          </Group>

          <Stack gap="xs">
            {items.map((item: RecommendationItem) => {
              const matchPercent = Math.round(item.score * 100);
              const metaSegments = formatGameMeta(item);

              return (
                <div key={item.id} className={classes.matchRow}>
                  <div className={classes.matchRank}>#{item.rank}</div>

                  <button
                    type="button"
                    className={classes.coverButton}
                    onClick={() => navigate(`/games/${item.game.id}`)}
                    aria-label={`Open ${item.game.name}`}
                  >
                    {item.game.background_image ? (
                      <img src={item.game.background_image} alt="" />
                    ) : (
                      <IconSparkles size={18} color="var(--mantine-color-dimmed)" />
                    )}
                  </button>

                  <div className={classes.matchBody}>
                    <Group justify="space-between" align="flex-start" gap="sm" wrap="nowrap" className={classes.matchTop}>
                      <div className={classes.matchInfo}>
                        <button
                          type="button"
                          className={classes.titleButton}
                          onClick={() => navigate(`/games/${item.game.id}`)}
                        >
                          {item.game.name}
                        </button>
                        <div className={classes.matchMeta}>
                          {metaSegments.map((segment, index) => (
                            <span key={`${item.id}-${index}`}>{segment}</span>
                          ))}
                        </div>
                      </div>

                      <div className={classes.scoreBlock}>
                        <div className={classes.scoreLabel}>Match</div>
                        <div className={classes.scoreValue}>{matchPercent}%</div>
                      </div>
                    </Group>

                    <div className={classes.scoreTrack}>
                      <div
                        className={classes.scoreFill}
                        style={{ width: `${Math.max(matchPercent, matchPercent > 0 ? 10 : 0)}%` }}
                      />
                    </div>

                    {item.explanation && (
                      <Text size="xs" className={classes.explanation}>
                        {item.explanation}
                      </Text>
                    )}

                    <Group justify="space-between" align="center" gap="sm" className={classes.matchFooter}>
                      <Text size="xs" c="dimmed" className={classes.matchReason}>
                        Ranked by overlap with your saved genres and tags.
                      </Text>

                      <Group gap={6} wrap="nowrap">
                        <Tooltip label="Helpful">
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="teal"
                            aria-label="Mark recommendation helpful"
                            onClick={() => submitFeedback({ item_id: item.id, is_helpful: true })}
                          >
                            <IconThumbUp size={14} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="Not helpful">
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            color="gray"
                            aria-label="Mark recommendation not helpful"
                            onClick={() => submitFeedback({ item_id: item.id, is_helpful: false })}
                          >
                            <IconThumbDown size={14} />
                          </ActionIcon>
                        </Tooltip>
                        <Button
                          size="xs"
                          variant="subtle"
                          color="ember"
                          rightSection={<IconArrowRight size={14} />}
                          onClick={() => navigate(`/games/${item.game.id}`)}
                        >
                          View
                        </Button>
                      </Group>
                    </Group>
                  </div>
                </div>
              );
            })}
          </Stack>
        </Paper>
      )}
    </Stack>
  );
}
