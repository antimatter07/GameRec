import {
  Paper,
  Text,
  Badge,
  Group,
  Stack,
  Chip,
  Divider,
} from '@mantine/core';
import {
  IconClock,
  IconTrophy,
  IconFlame,
  IconChartBar,
} from '@tabler/icons-react';
import { EmotionType, EMOTION_CONFIG } from '../../types/journal';
import type { JournalStats, EmotionStats } from '../../types/journal';
import classes from './Journal.module.css';

// ─── Mantine color → CSS variable ────────────────────────────────────────────
const EMOTION_CSS_COLORS: Record<EmotionType, string> = {
  [EmotionType.FRUSTRATED]:   'var(--mantine-color-orange-6)',
  [EmotionType.HAPPY]:        'var(--mantine-color-yellow-5)',
  [EmotionType.SAD]:          'var(--mantine-color-blue-4)',
  [EmotionType.ANGRY]:        'var(--mantine-color-red-6)',
  [EmotionType.RELAXED]:      'var(--mantine-color-teal-5)',
  [EmotionType.BORED]:        'var(--mantine-color-gray-5)',
  [EmotionType.PROUD]:        'var(--mantine-color-yellow-7)',
  [EmotionType.CREEPED_OUT]:  'var(--mantine-color-grape-6)',
  [EmotionType.DISAPPOINTED]: 'var(--mantine-color-gray-6)',
};

const GENRE_COLORS = [
  '#d4674d',
  'var(--mantine-color-teal-5)',
  '#e0b957',
  '#5b8def',
  'var(--mantine-color-pink-5)',
  'var(--mantine-color-orange-5)',
  'var(--mantine-color-green-5)',
  'var(--mantine-color-gray-5)',
];

// ─── Top Metrics Row ──────────────────────────────────────────────────────────

interface MetricCardsProps {
  stats: JournalStats;
}

export function MetricCards({ stats }: MetricCardsProps) {
  return (
    <div className={classes.metricsGrid}>
      <Paper className={classes.metricCard} p="md" radius="md" withBorder>
        <div className={classes.metricIcon} style={{ background: 'rgba(212, 103, 77, 0.14)' }}>
          <IconClock size={18} color="#d4674d" />
        </div>
        <div className={classes.metricLabel}>Hours this week</div>
        <div className={classes.metricValue} style={{ color: '#e97d61' }}>
          {stats.total_hours_this_week.toFixed(1)}
        </div>
        <div className={classes.metricSub}>
          <Badge size="xs" variant="light" color={stats.hours_change_pct_week >= 0 ? 'teal' : 'red'}>
            {stats.hours_change_pct_week >= 0 ? '↑' : '↓'} {Math.abs(stats.hours_change_pct_week)}%
          </Badge>
          <span>vs last week</span>
        </div>
      </Paper>

      <Paper className={classes.metricCard} p="md" radius="md" withBorder>
        <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-teal-light)' }}>
          <IconTrophy size={18} color="var(--mantine-color-teal-5)" />
        </div>
        <div className={classes.metricLabel}>Games completed</div>
        <div className={classes.metricValue} style={{ color: 'var(--mantine-color-teal-4)' }}>
          {stats.games_completed}
          <Text span size="sm" c="dimmed" fw={400}> / {stats.games_in_backlog} backlog</Text>
        </div>
        <div className={classes.metricSub}>
          {stats.games_in_backlog > 0
            ? `${Math.round((stats.games_completed / (stats.games_completed + stats.games_in_backlog)) * 100)}% clearance`
            : 'No backlog'}
        </div>
      </Paper>

      <Paper className={classes.metricCard} p="md" radius="md" withBorder>
        <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-yellow-light)' }}>
          <IconFlame size={18} color="var(--mantine-color-yellow-5)" />
        </div>
        <div className={classes.metricLabel}>Current streak</div>
        <div className={classes.metricValue} style={{ color: 'var(--mantine-color-yellow-4)' }}>
          {stats.current_streak_days}
          <Text span size="sm" c="dimmed" fw={400}> days</Text>
        </div>
        <div className={classes.metricSub}>Longest: {stats.longest_streak_days} days</div>
      </Paper>

      <Paper className={classes.metricCard} p="md" radius="md" withBorder>
        <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-blue-light)' }}>
          <IconChartBar size={18} color="var(--mantine-color-blue-5)" />
        </div>
        <div className={classes.metricLabel}>Sessions this month</div>
        <div className={classes.metricValue} style={{ color: 'var(--mantine-color-blue-4)' }}>
          {stats.sessions_this_month}
        </div>
        <div className={classes.metricSub}>
          <Badge size="xs" variant="light" color={stats.sessions_change_pct_month >= 0 ? 'teal' : 'red'}>
            {stats.sessions_change_pct_month >= 0 ? '↑' : '↓'} {Math.abs(stats.sessions_change_pct_month)}%
          </Badge>
          <span>vs last month</span>
        </div>
      </Paper>
    </div>
  );
}

// ─── Genre Hours Chart ────────────────────────────────────────────────────────

interface GenreChartProps {
  genres: JournalStats['top_genres_this_month'];
}

export function GenreHoursChart({ genres }: GenreChartProps) {
  if (genres.length === 0) {
    return (
      <Text size="sm" c="dimmed" ta="center" py="xl">
        No sessions logged this month yet.
      </Text>
    );
  }

  const maxHours = Math.max(...genres.map((g) => g.hours));

  return (
    <Stack gap={0}>
      {genres.slice(0, 8).map((g, i) => (
        <div key={g.genre} className={classes.genreRow}>
          <span className={classes.genreLabel}>{g.genre}</span>
          <div className={classes.genreTrack}>
            <div
              className={classes.genreFill}
              style={{
                width: `${(g.hours / maxHours) * 100}%`,
                background: GENRE_COLORS[i % GENRE_COLORS.length],
              }}
            >
              {g.hours.toFixed(1)}h
            </div>
          </div>
        </div>
      ))}
    </Stack>
  );
}

// ─── Weekly Activity + Streak Ring ────────────────────────────────────────────

interface WeeklyActivityProps {
  dailyHours:    JournalStats['daily_hours_this_week'];
  currentStreak: number;
  longestStreak: number;
}

export function WeeklyActivityCard({ dailyHours, currentStreak, longestStreak }: WeeklyActivityProps) {
  const maxH  = Math.max(...dailyHours.map((d) => d.hours), 1);
  const today = new Date().toLocaleDateString('en-US', { weekday: 'short' });

  const streakPct     = Math.min((currentStreak / 30) * 100, 100);
  const circumference = 2 * Math.PI * 42;
  const dashOffset    = circumference - (streakPct / 100) * circumference;

  return (
    <Stack gap="md">
      <div className={classes.weeklyGrid}>
        {dailyHours.map((d) => {
          const opacity = Math.max(0.06, (d.hours / maxH) * 0.35);
          const isToday = d.day === today;
          return (
            <div
              key={d.day}
              className={`${classes.dayCell} ${isToday ? classes.dayCellActive : ''}`}
              style={{ background: `rgba(124, 92, 252, ${opacity})` }}
            >
              <span className={classes.dayLabel}>{d.day}</span>
              <span className={classes.dayHours}>{d.hours.toFixed(1)}</span>
            </div>
          );
        })}
      </div>

      <Divider />

      <div style={{ textAlign: 'center' }}>
        <div className={classes.streakRing}>
          <svg viewBox="0 0 100 100" width="100%" height="100%" className={classes.streakRingSvg}>
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--mantine-color-dark-5)" strokeWidth="6" />
            <circle
              cx="50" cy="50" r="42" fill="none"
              stroke="#d4674d"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
            />
          </svg>
          <div className={classes.streakCenter}>
            <span className={classes.streakNumber}>{currentStreak}</span>
            <span className={classes.streakUnit}>day streak</span>
          </div>
        </div>
        <Text size="xs" c="dimmed">
          Longest streak:{' '}
          <Text span fw={600} c="yellow.5">{longestStreak} days</Text>
        </Text>
      </div>
    </Stack>
  );
}

// ─── Emotion Summary ──────────────────────────────────────────────────────────

interface EmotionSummaryProps {
  emotionStats:   EmotionStats | null;
  dominantEmotion: EmotionType | null;
  coveragePct:    number | null;
  totalSessions:  number;
}

export function EmotionSummaryCard({
  emotionStats,
  dominantEmotion,
  coveragePct,
  totalSessions,
}: EmotionSummaryProps) {
  const frequency = emotionStats?.frequency ?? [];

  if (!dominantEmotion && frequency.length === 0) {
    return (
      <Text size="sm" c="dimmed" ta="center" py="lg">
        Log sessions with emotions to see your mood profile here.
      </Text>
    );
  }

  return (
    <Stack gap="sm">
      {dominantEmotion && (
        <div style={{ textAlign: 'center', marginBottom: 4 }}>
          <Text size="sm" fw={600} c="#e97d61">
            Dominant mood: {EMOTION_CONFIG[dominantEmotion]?.label}
          </Text>
          <Text size="xs" c="dimmed">
            Across {totalSessions} sessions this month
            {coveragePct !== null && ` (${Math.round(coveragePct)}% with emotions logged)`}
          </Text>
        </div>
      )}

      {frequency.length > 0 && (
        <div className={classes.emotionChipGrid}>
          {frequency.slice(0, 9).map((item) => {
            const config   = EMOTION_CONFIG[item.emotion];
            const cssColor = EMOTION_CSS_COLORS[item.emotion];
            if (!config) return null;
            return (
              <Chip key={item.emotion} checked={false} variant="outline" color={config.color} size="xs">
                <Group gap={4} wrap="nowrap">
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: cssColor, flexShrink: 0 }} />
                  {config.label}
                  <span className={classes.emotionPct}>{Math.round(item.percentage)}%</span>
                </Group>
              </Chip>
            );
          })}
        </div>
      )}

      {emotionStats?.top_positive_game && (
        <div className={classes.insightBox}>
          Your happiest game:{' '}
          <Text span fw={600} c="var(--mantine-color-text)">{emotionStats.top_positive_game.game_title}</Text>
          {emotionStats.top_negative_game && (
            <>
              . Most frustrating:{' '}
              <Text span fw={600} c="var(--mantine-color-text)">{emotionStats.top_negative_game.game_title}</Text>{' '}
              but you kept going.
            </>
          )}
        </div>
      )}
    </Stack>
  );
}

// ─── Backlog Progress ─────────────────────────────────────────────────────────

interface BacklogProgressProps {
  completed: number;
  playing:   number;
  backlog:   number;
}

export function BacklogProgressCard({ completed, playing, backlog }: BacklogProgressProps) {
  const total        = completed + playing + backlog;
  const completedPct = total > 0 ? (completed / total) * 100 : 0;
  const playingPct   = total > 0 ? (playing / total) * 100 : 0;
  const backlogPct   = total > 0 ? (backlog / total) * 100 : 0;

  return (
    <Stack gap="md">
      <div className={classes.backlogMiniCards}>
        <div className={classes.backlogMiniCard}>
          <div className={classes.backlogMiniValue} style={{ color: 'var(--mantine-color-teal-4)' }}>{completed}</div>
          <div className={classes.backlogMiniLabel}>Completed</div>
        </div>
        <div className={classes.backlogMiniCard}>
          <div className={classes.backlogMiniValue} style={{ color: '#e97d61' }}>{playing}</div>
          <div className={classes.backlogMiniLabel}>Playing</div>
        </div>
        <div className={classes.backlogMiniCard}>
          <div className={classes.backlogMiniValue} style={{ color: 'var(--mantine-color-dimmed)' }}>{backlog}</div>
          <div className={classes.backlogMiniLabel}>Backlog</div>
        </div>
      </div>

      <div className={classes.backlogBarContainer}>
        <div className={classes.backlogBarFill} style={{ width: `${completedPct}%`, background: 'var(--mantine-color-teal-5)', borderRadius: '4px 0 0 4px' }} />
        <div className={classes.backlogBarFill} style={{ width: `${playingPct}%`, background: '#d4674d' }} />
        <div className={classes.backlogBarFill} style={{ width: `${backlogPct}%`, background: 'var(--mantine-color-dark-5)', borderRadius: '0 4px 4px 0' }} />
      </div>

      <Group gap="md">
        {[
          { color: 'var(--mantine-color-teal-5)',   label: 'Completed' },
          { color: '#d4674d', label: 'Playing'   },
          { color: 'var(--mantine-color-dark-5)',   label: 'Backlog'   },
        ].map(({ color, label }) => (
          <Group key={label} gap={4}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
            <Text size="xs" c="dimmed">{label}</Text>
          </Group>
        ))}
      </Group>
    </Stack>
  );
}
