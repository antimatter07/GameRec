import type { KeyboardEvent } from 'react';
import { Badge, Card, Group, Image, Rating, Stack, Text, Tooltip } from '@mantine/core';
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

function getVisibleGenres(genres: GameListItem['genres'], maxVisible = 2) {
  const genreNames = genres.map((genre) => genre.name).filter(Boolean);
  const visibleGenres = genreNames.slice(0, maxVisible);
  const hiddenGenres = genreNames.slice(maxVisible);

  return {
    visibleGenres,
    hiddenGenres,
    hiddenCount: hiddenGenres.length,
    fullGenreLabel: genreNames.join(', '),
  };
}

export function GameCard({ game, showAdd = false }: GameCardProps) {
  const { data: library } = useLibrary();
  const navigate = useNavigate();

  const libraryEntry = library?.find((entry) => entry.game.id === game.id) ?? null;
  const inLibrary = libraryEntry !== null;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;
  const primaryPlatform = game.platforms[0]?.name;
  const { visibleGenres, hiddenGenres, hiddenCount, fullGenreLabel } = getVisibleGenres(game.genres);
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

        <div className={classes.metaBlock}>
          <div className={classes.metaPrimary}>
            <span>{releaseYear ?? 'TBA'}</span>
            {primaryPlatform && (
              <>
                <span aria-hidden="true">·</span>
                <span className={classes.platformText}>{primaryPlatform}</span>
              </>
            )}
          </div>

          {visibleGenres.length > 0 && (
            <div className={classes.genreRow} aria-label={`Genres: ${fullGenreLabel}`}>
              {visibleGenres.map((genre, index) => (
                <span className={classes.genreGroup} key={`${genre}-${index}`}>
                  {index > 0 && <span aria-hidden="true">·</span>}
                  <span className={classes.genreText}>{genre}</span>
                </span>
              ))}
              {hiddenCount > 0 && (
                <Tooltip label={fullGenreLabel} withArrow openDelay={150}>
                  <span
                    className={classes.moreGenresChip}
                    title={fullGenreLabel}
                    tabIndex={0}
                    aria-label={`Additional genres: ${hiddenGenres.join(', ')}`}
                  >
                    +{hiddenCount}
                  </span>
                </Tooltip>
              )}
            </div>
          )}
        </div>

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
