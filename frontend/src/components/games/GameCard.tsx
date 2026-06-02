import type { KeyboardEvent } from 'react';
import { Badge, Card, Group, Image, Rating, Stack, Text } from '@mantine/core';
import { IconClock, IconFlame, IconSparkles, IconStar } from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { useLibrary } from '../../hooks/useLibrary';
import type { GameListItem } from '../../types/game';
import { SaveToLibraryButton } from './SaveToLibraryButton';
import classes from './GameCard.module.css';

interface GameCardProps {
  game: GameListItem;
  /** Show an "Add to Library" button — omit on the library page */
  showAdd?: boolean;
}

function getDiscoverySignal(game: GameListItem, inLibrary: boolean) {
  const hours = game.hltb_main_hours ?? game.playtime;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;
  const currentYear = new Date().getFullYear();

  if (inLibrary) {
    return { label: 'In your library', tone: 'teal', icon: IconSparkles };
  }

  if (hours !== null && hours <= 12) {
    return { label: 'Short backlog pick', tone: 'blue', icon: IconClock };
  }

  if (game.rating !== null && game.rating >= 4.25) {
    return { label: 'Highly rated', tone: 'yellow', icon: IconStar };
  }

  if (releaseYear !== null && releaseYear >= currentYear - 1) {
    return { label: 'Recent release', tone: 'ember', icon: IconFlame };
  }

  return { label: 'Discovery pick', tone: 'gray', icon: IconSparkles };
}

export function GameCard({ game, showAdd = false }: GameCardProps) {
  const { data: library } = useLibrary();
  const navigate = useNavigate();

  const libraryEntry = library?.find((entry) => entry.game.id === game.id) ?? null;
  const inLibrary = libraryEntry !== null;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;
  const primaryGenre = game.genres[0]?.name;
  const primaryPlatform = game.platforms[0]?.name;
  const metaItems = [releaseYear ?? 'TBA', primaryGenre, primaryPlatform].filter(Boolean).join(' / ');
  const playtimeLabel = game.hltb_main_hours
    ? `${Math.round(game.hltb_main_hours)}h main`
    : game.playtime
      ? `${game.playtime}h avg`
      : null;
  const signal = getDiscoverySignal(game, inLibrary);
  const SignalIcon = signal.icon;

  const openGame = () => navigate(`/games/${game.id}`);
  const openGameFromKeyboard = (event: KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openGame();
    }
  };

  return (
    <Card
      className={classes.card}
      padding="sm"
      radius="md"
      withBorder
    >
      <Card.Section className={classes.imageSection}>
        <button
          type="button"
          className={classes.coverButton}
          onClick={openGame}
          onKeyDown={openGameFromKeyboard}
          aria-label={`Open ${game.name}`}
        >
          <Image
            src={game.background_image ?? undefined}
            alt=""
            className={classes.image}
            fallbackSrc="https://placehold.co/400x200?text=No+Image"
          />
        </button>
        <div className={classes.imageShade} />
        {playtimeLabel && (
          <Badge className={classes.playtimeBadge} variant="filled" size="sm">
            {playtimeLabel}
          </Badge>
        )}
        {showAdd && (
          <div className={classes.saveControl}>
            <SaveToLibraryButton
              game={game}
              libraryEntry={libraryEntry}
              className={classes.saveIcon}
              size="lg"
              iconOnly
            />
          </div>
        )}
      </Card.Section>

      <Stack gap={10} mt="sm" className={classes.body}>
        <button
          type="button"
          className={classes.titleButton}
          onClick={openGame}
          onKeyDown={openGameFromKeyboard}
        >
          {game.name}
        </button>

        <Text size="sm" c="dimmed" className={classes.meta}>
          {metaItems}
        </Text>

        <Badge
          className={classes.signalBadge}
          color={signal.tone}
          variant="light"
          leftSection={<SignalIcon size={12} stroke={1.8} />}
        >
          {signal.label}
        </Badge>

        <Group gap={8} align="center" className={classes.ratingRow}>
          <Rating value={(game.rating ?? 0) / 2} fractions={2} readOnly size="sm" color="yellow" />
          <Text size="sm" c="dimmed" className={classes.ratingValue}>
            {game.rating !== null ? game.rating.toFixed(1) : 'NR'}
          </Text>
        </Group>

      </Stack>
    </Card>
  );
}
