import { Button, Menu } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBookmark, IconChevronDown, IconTrash } from '@tabler/icons-react';
import { isAxiosError } from 'axios';
import type { KeyboardEvent, MouseEvent } from 'react';
import { useAddToLibrary, useRemoveFromLibrary } from '../../hooks/useLibrary';
import type { GameListItem } from '../../types/game';
import type { LibraryEntry, LibraryStatus } from '../../types/library';

const STATUS_OPTIONS: Array<{ value: LibraryStatus; label: string }> = [
  { value: 'wishlist', label: 'Wishlist' },
  { value: 'backlog', label: 'Backlog' },
  { value: 'playing', label: 'Playing' },
  { value: 'completed', label: 'Completed' },
  { value: 'dropped', label: 'Dropped' },
];

interface SaveToLibraryButtonProps {
  game: GameListItem;
  libraryEntry?: LibraryEntry | null;
  fullWidth?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: string;
  className?: string;
}

export function SaveToLibraryButton({
  game,
  libraryEntry = null,
  fullWidth = false,
  size = 'md',
  variant = 'filled',
  className,
}: SaveToLibraryButtonProps) {
  const addToLibrary = useAddToLibrary();
  const removeFromLibrary = useRemoveFromLibrary();

  const stopCardClick = (event: MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
  };
  const stopCardKeyDown = (event: KeyboardEvent) => {
    event.stopPropagation();
  };

  const handleSaveAs = async (status: LibraryStatus) => {
    try {
      await addToLibrary.mutateAsync({ game_id: game.id, status });
      notifications.show({ color: 'green', message: `${game.name} saved to ${status}` });
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail = err.response?.data?.detail as string | undefined;
        notifications.show({
          color: err.response?.status === 409 ? 'yellow' : 'red',
          message: err.response?.status === 409 ? 'Already in your library' : detail ?? 'Failed to save game',
        });
      } else {
        notifications.show({ color: 'red', message: 'Failed to save game' });
      }
    }
  };

  const handleRemove = async (event: MouseEvent) => {
    stopCardClick(event);
    if (!libraryEntry) return;

    try {
      await removeFromLibrary.mutateAsync(libraryEntry.id);
      notifications.show({ color: 'red', message: `${game.name} removed from library` });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to remove from library' });
    }
  };

  if (libraryEntry) {
    return (
      <Button
        className={className}
        size={size}
        variant={variant}
        leftSection={<IconTrash size={15} />}
        onClick={handleRemove}
        onKeyDown={stopCardKeyDown}
        loading={removeFromLibrary.isPending}
        fullWidth={fullWidth}
      >
        Remove
      </Button>
    );
  }

  return (
    <Menu shadow="md" width={180}>
      <Menu.Target>
        <Button
          className={className}
          size={size}
          variant={variant}
          leftSection={<IconBookmark size={15} />}
          rightSection={<IconChevronDown size={14} />}
          onClick={stopCardClick}
          onKeyDown={stopCardKeyDown}
          loading={addToLibrary.isPending}
          fullWidth={fullWidth}
        >
          Save as
        </Button>
      </Menu.Target>
      <Menu.Dropdown onClick={stopCardClick}>
        {STATUS_OPTIONS.map((option) => (
          <Menu.Item key={option.value} onClick={() => handleSaveAs(option.value)}>
            {option.label}
          </Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  );
}
