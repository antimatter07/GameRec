import { ActionIcon, Button, Menu } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBookmark, IconCheck, IconChevronDown, IconPlus, IconTrash } from '@tabler/icons-react';
import { isAxiosError } from 'axios';
import type { KeyboardEvent, MouseEvent } from 'react';
import { useAddToLibrary, useRemoveFromLibrary, useUpdateLibraryEntry } from '../../hooks/useLibrary';
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
  iconOnly?: boolean;
}

export function SaveToLibraryButton({
  game,
  libraryEntry = null,
  fullWidth = false,
  size = 'md',
  variant = 'filled',
  className,
  iconOnly = false,
}: SaveToLibraryButtonProps) {
  const addToLibrary = useAddToLibrary();
  const removeFromLibrary = useRemoveFromLibrary();
  const updateLibraryEntry = useUpdateLibraryEntry();

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

  const handleUpdateStatus = async (status: LibraryStatus) => {
    if (!libraryEntry) return;

    try {
      await updateLibraryEntry.mutateAsync({ id: libraryEntry.id, updates: { status } });
      notifications.show({ color: 'teal', message: `${game.name} moved to ${status}` });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to update library status' });
    }
  };

  if (libraryEntry) {
    if (iconOnly) {
      return (
        <Menu shadow="md" width={190} position="bottom-end" withArrow>
          <Menu.Target>
            <ActionIcon
              className={className}
              size={size}
              radius="sm"
              variant="filled"
              color="teal"
              onClick={stopCardClick}
              onKeyDown={stopCardKeyDown}
              loading={removeFromLibrary.isPending || updateLibraryEntry.isPending}
              aria-label={`Manage ${game.name} in library`}
              title={`Saved to ${libraryEntry.status}`}
            >
              <IconCheck size={17} stroke={2} />
            </ActionIcon>
          </Menu.Target>
          <Menu.Dropdown onClick={stopCardClick}>
            {STATUS_OPTIONS.map((option) => (
              <Menu.Item
                key={option.value}
                disabled={libraryEntry.status === option.value}
                onClick={() => handleUpdateStatus(option.value)}
              >
                {libraryEntry.status === option.value ? `${option.label} current` : `Move to ${option.label}`}
              </Menu.Item>
            ))}
            <Menu.Divider />
            <Menu.Item color="red.4" leftSection={<IconTrash size={14} />} onClick={handleRemove}>
              Remove from library
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      );
    }

    return (
      <Menu shadow="md" width={190}>
        <Menu.Target>
          <Button
            className={className}
            size={size}
            variant={variant}
            leftSection={<IconCheck size={15} />}
            rightSection={<IconChevronDown size={14} />}
            onClick={stopCardClick}
            onKeyDown={stopCardKeyDown}
            loading={removeFromLibrary.isPending || updateLibraryEntry.isPending}
            fullWidth={fullWidth}
          >
            Saved
          </Button>
        </Menu.Target>
        <Menu.Dropdown onClick={stopCardClick}>
          {STATUS_OPTIONS.map((option) => (
            <Menu.Item
              key={option.value}
              disabled={libraryEntry.status === option.value}
              onClick={() => handleUpdateStatus(option.value)}
            >
              {libraryEntry.status === option.value ? `${option.label} current` : `Move to ${option.label}`}
            </Menu.Item>
          ))}
          <Menu.Divider />
          <Menu.Item color="red.4" leftSection={<IconTrash size={14} />} onClick={handleRemove}>
            Remove from library
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
    );
  }

  if (iconOnly) {
    return (
      <Menu shadow="md" width={180} position="bottom-end" withArrow>
        <Menu.Target>
          <ActionIcon
            className={className}
            size={size}
            radius="sm"
            variant="filled"
            color="ember"
            onClick={stopCardClick}
            onKeyDown={stopCardKeyDown}
            loading={addToLibrary.isPending}
            aria-label={`Save ${game.name} to library`}
            title="Save to library"
          >
            <IconPlus size={18} stroke={2.1} />
          </ActionIcon>
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
