import {
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  Progress,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { useRecommendations, useSubmitFeedback } from '../../hooks/useRecommendations';
import { useAuthStore } from '../../store/authStore';
import { GameCard } from '../../components/games/GameCard';
import type { RecommendationItem } from '../../types/recommendation';

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

  const { data, isLoading, isError } = useRecommendations();
  const { mutate: submitFeedback } = useSubmitFeedback();

  if (isLoading) return <Center h={400}><Loader /></Center>;
  if (isError)   return <Text c="red">Failed to load recommendations.</Text>;

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Your Recommendations</Title>
        {/* TODO: Add "Refresh" button */}
        {isPremium && (
          <Badge variant="gradient" gradient={{ from: 'violet', to: 'cyan' }}>
            Premium
          </Badge>
        )}
      </Group>

      {!data || data.items.length === 0 ? (
        <Text c="dimmed">
          Add and rate some games in your library to get personalized recommendations.
        </Text>
      ) : (
        <Stack gap="md">
          {data.items.map((item: RecommendationItem) => (
            <Paper key={item.rank} p="md" withBorder radius="md">
              <Group align="flex-start" wrap="nowrap">
                <Text fw={700} size="xl" w={32} ta="center" c="dimmed">
                  #{item.rank}
                </Text>

                <Stack gap="xs" style={{ flex: 1 }}>
                  <GameCard game={item.game} />

                  <Group gap="xs">
                    <Text size="xs" c="dimmed">
                      Match:
                    </Text>
                    <Progress
                      value={item.score * 100}
                      size="sm"
                      style={{ flex: 1 }}
                      color="teal"
                    />
                    <Text size="xs" fw={600}>
                      {(item.score * 100).toFixed(0)}%
                    </Text>
                  </Group>

                  {/* Premium: LLM explanation */}
                  {item.explanation && (
                    <Text size="sm" c="dimmed" fs="italic">
                      "{item.explanation}"
                    </Text>
                  )}

                  {/* Feedback buttons */}
                  <Group gap="xs">
                    <Button
                      size="xs"
                      variant="light"
                      color="teal"
                      onClick={() => submitFeedback({ item_id: item.id, is_helpful: true })}
                    >
                      👍 Helpful
                    </Button>
                    <Button
                      size="xs"
                      variant="light"
                      color="red"
                      onClick={() => submitFeedback({ item_id: item.id, is_helpful: false })}
                    >
                      👎 Not helpful
                    </Button>
                  </Group>
                </Stack>
              </Group>
            </Paper>
          ))}
        </Stack>
      )}
    </Stack>
  );
}
