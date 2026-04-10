import { ActionIcon, Box, Image, Stack, Text } from '@mantine/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { IconX } from '@tabler/icons-react';
import type { PlayQueueEntry } from '../../types/playQueue';
import { useDequeueGame } from '../../hooks/usePlayQueue';

interface PlayQueueItemProps {
  item: PlayQueueEntry;
}

const CARD_WIDTH = 140;

export function PlayQueueItem({ item }: PlayQueueItemProps) {
  const { game } = item.entry;
  const dequeue = useDequeueGame();

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.entry_id,
  });

  const playtimeHours = game.hltb_main_hours ?? game.playtime ?? null;

  return (
    <Box
      ref={setNodeRef}
      style={{
        width: CARD_WIDTH,
        flexShrink: 0,
        position: 'relative',
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
        cursor: 'grab',
      }}
      {...attributes}
      {...listeners}
    >
      {/* Position badge */}
      <Box
        style={{
          position: 'absolute',
          top: 6,
          left: 6,
          zIndex: 2,
          background: 'rgba(0,0,0,0.7)',
          color: '#fff',
          borderRadius: 4,
          padding: '1px 6px',
          fontSize: 11,
          fontWeight: 700,
          lineHeight: '18px',
        }}
      >
        {item.position}
      </Box>

      {/* Remove button */}
      <ActionIcon
        size="xs"
        variant="filled"
        color="dark"
        style={{ position: 'absolute', top: 6, right: 6, zIndex: 2 }}
        onClick={(e) => {
          e.stopPropagation();
          dequeue.mutate(item.entry_id);
        }}
        loading={dequeue.isPending}
        aria-label={`Remove ${game.name} from queue`}
      >
        <IconX size={10} />
      </ActionIcon>

      <Image
        src={game.background_image ?? undefined}
        w={CARD_WIDTH}
        h={100}
        radius="sm"
        fallbackSrc="https://placehold.co/140x100?text=?"
        style={{ objectFit: 'cover', display: 'block' }}
      />

      <Stack gap={2} mt={4} px={2}>
        <Text size="xs" fw={600} lineClamp={2} style={{ lineHeight: 1.3 }}>
          {game.name}
        </Text>
        {playtimeHours != null && (
          <Text size="xs" c="dimmed">~{Number(playtimeHours).toFixed(0)}h</Text>
        )}
      </Stack>
    </Box>
  );
}
