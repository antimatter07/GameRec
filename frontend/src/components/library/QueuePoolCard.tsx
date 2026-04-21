import { ActionIcon, Badge, Box, Image, Stack, Text } from '@mantine/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { IconPlus } from '@tabler/icons-react';
import type { LibraryEntry, LibraryStatus } from '../../types/library';

interface QueuePoolCardProps {
  entry: LibraryEntry;
  onPlusClick: () => void;
}

const CARD_WIDTH = 140;

const STATUS_COLORS: Record<LibraryStatus, string> = {
  playing:   'teal',
  completed: 'blue',
  backlog:   'gray',
  dropped:   'red',
};

export function QueuePoolCard({ entry, onPlusClick }: QueuePoolCardProps) {
  const { game } = entry;

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `pool-${entry.id}`,
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
      {/* Status badge */}
      <Box
        style={{
          position: 'absolute',
          top: 6,
          left: 6,
          zIndex: 2,
        }}
      >
        <Badge size="xs" color={STATUS_COLORS[entry.status]} variant="filled">
          {entry.status}
        </Badge>
      </Box>

      {/* Add-to-queue button */}
      <ActionIcon
        size="xs"
        variant="filled"
        color="grape"
        style={{ position: 'absolute', top: 6, right: 6, zIndex: 2 }}
        onClick={(e) => {
          e.stopPropagation();
          onPlusClick();
        }}
        onPointerDown={(e) => e.stopPropagation()}
        aria-label={`Add ${game.name} to queue`}
      >
        <IconPlus size={12} />
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
