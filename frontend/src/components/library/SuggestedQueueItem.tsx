import type { QueueSuggestionItem } from '../../types/playQueue';
import { QueueCard } from './QueueCard';

interface SuggestedQueueItemProps {
  item: QueueSuggestionItem;
}

export function SuggestedQueueItem({ item }: SuggestedQueueItemProps) {
  return (
    <QueueCard
      game={item.entry.game}
      rating={item.entry.rating}
      label={`#${item.suggested_position}`}
      reason={item.reason}
      readOnly
    />
  );
}
