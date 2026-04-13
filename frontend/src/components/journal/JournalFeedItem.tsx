import { Text, Badge, Tooltip, Image } from '@mantine/core';
import { IconTrophy } from '@tabler/icons-react';
import { EmotionType, EMOTION_CONFIG } from '../../types/journal';
import type { SessionLog } from '../../types/journal';
import classes from './Journal.module.css';

// ─── Mantine color string → CSS variable mapping ─────────────────────────────
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

function formatDuration(minutes: number | null): string {
  if (!minutes) return '—';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  const now  = new Date();
  const diffMs   = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return `Today, ${date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
  }
  if (diffDays === 1) {
    return `Yesterday, ${date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
  }
  return date.toLocaleDateString([], {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

interface JournalFeedItemProps {
  session:  SessionLog;
  onClick?: () => void;
}

export function JournalFeedItem({ session, onClick }: JournalFeedItemProps) {
  return (
    <div className={classes.sessionItem} onClick={onClick}>
      <div className={classes.sessionCover}>
        {session.game_cover_url ? (
          <Image
            src={session.game_cover_url}
            alt={session.game_title ?? 'Game'}
            w={44}
            h={58}
            fit="cover"
          />
        ) : (
          <Text size="lg">🎮</Text>
        )}
      </div>

      <div className={classes.sessionInfo}>
        <div className={classes.sessionTitle}>
          {session.game_title ?? `Game #${session.game_id}`}
        </div>
        <div className={classes.sessionMeta}>
          <span>{formatDate(session.started_at)}</span>
          {session.game_genres && session.game_genres.length > 0 && (
            <>
              <span>·</span>
              <span>{session.game_genres.slice(0, 2).join(' / ')}</span>
            </>
          )}
          {session.is_milestone && session.milestone_label && (
            <Badge
              size="xs"
              variant="light"
              color="yellow"
              leftSection={<IconTrophy size={10} />}
            >
              {session.milestone_label}
            </Badge>
          )}
        </div>
      </div>

      {/* Emotion dots */}
      {session.emotions && session.emotions.length > 0 && (
        <div className={classes.sessionEmotionDots}>
          {session.emotions.slice(0, 5).map((emotion, i) => (
            <Tooltip
              key={`${emotion}-${i}`}
              label={EMOTION_CONFIG[emotion]?.label ?? emotion}
              withArrow
              position="top"
            >
              <div
                className={classes.emotionDot}
                style={{
                  background: EMOTION_CSS_COLORS[emotion] ?? 'var(--mantine-color-gray-5)',
                }}
              />
            </Tooltip>
          ))}
        </div>
      )}

      <div className={classes.sessionDuration}>
        {formatDuration(session.duration_minutes)}
      </div>
    </div>
  );
}
