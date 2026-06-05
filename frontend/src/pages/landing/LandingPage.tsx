import {
  IconArrowRight,
  IconBook2,
  IconDeviceGamepad2,
  IconListCheck,
  IconSparkles,
} from '@tabler/icons-react';
import { Link } from 'react-router';
import heroArt from '../../assets/landing/hero_art_landing_transparent.png';
import gameRadarIcon from '../../assets/landing/icons/game-radar-icon-transparent.png';
import journalIcon from '../../assets/landing/icons/journal-icon-transparent.png';
import playerGraphIcon from '../../assets/landing/icons/player-graph-icon-transparent.png';
import starIcon from '../../assets/landing/icons/star-icon-transparent.png';
import classes from './LandingPage.module.css';

const posterCards = [
  { title: 'Ashen Gate', meta: 'Atmospheric adventure', tone: 'ember' },
  { title: 'Low Tide Signal', meta: 'Quiet exploration', tone: 'teal' },
  { title: 'Vesper Drift', meta: 'Story rich', tone: 'gold' },
  { title: 'Iron Orchard', meta: 'Tactical challenge', tone: 'blue' },
];

const features = [
  {
    title: 'Taste-aware recommendations',
    body: 'See picks shaped by the games you finish, abandon, rate, save, and write about.',
    icon: gameRadarIcon,
    iconAlt: '',
    signal: 'Game radar',
    accent: 'radar',
  },
  {
    title: 'Understand your player pattern',
    body: 'Spot the genres, moods, session lengths, and pacing you keep returning to.',
    icon: playerGraphIcon,
    iconAlt: '',
    signal: 'Taste graph',
    accent: 'graph',
  },
  {
    title: 'Keep ratings useful',
    body: 'Turn stars, saves, and completions into memory instead of another static list.',
    icon: starIcon,
    iconAlt: '',
    signal: 'Library memory',
    accent: 'star',
  },
  {
    title: 'Journal every play session',
    body: 'Capture why a game stayed with you, where you stopped, and what to return to next.',
    icon: journalIcon,
    iconAlt: '',
    signal: 'Session journal',
    accent: 'journal',
  },
];

const steps = [
  'Add or import games',
  'Rate, journal, and queue',
  'Get smart recommendations',
  'Return with context preserved',
];

function BrandMark() {
  return (
    <span className={classes.brandMark} aria-hidden="true">
      <IconDeviceGamepad2 size={20} stroke={1.9} />
    </span>
  );
}

function PosterCard({ title, meta, tone }: (typeof posterCards)[number]) {
  return (
    <article className={`${classes.posterCard} ${classes[`poster_${tone}`]}`}>
      <div className={classes.posterArt} aria-hidden="true" />
      <div className={classes.posterBody}>
        <strong>{title}</strong>
        <span>{meta}</span>
      </div>
    </article>
  );
}

function ReasonPanel({ compact = false }: { compact?: boolean }) {
  return (
    <article className={`${classes.reasonPanel} ${compact ? classes.reasonPanelCompact : ''}`}>
      <div className={classes.panelKicker}>
        <IconSparkles size={14} stroke={1.9} />
        Why this matches you
      </div>
      <h3>Ashen Gate fits your current pattern.</h3>
      <ul>
        <li>You keep finishing atmospheric worlds with deliberate combat.</li>
        <li>Your journal notes favor quiet discovery after long workdays.</li>
        <li>It is shorter than your paused epics, so it can actually move.</li>
      </ul>
    </article>
  );
}

function FeatureIconStage({ feature }: { feature: (typeof features)[number] }) {
  return (
    <div className={`${classes.featureIconStage} ${classes[`featureIcon_${feature.accent}`]}`}>
      <img src={feature.icon} alt={feature.iconAlt} aria-hidden="true" loading="lazy" />
      <span>{feature.signal}</span>
    </div>
  );
}

export default function LandingPage() {
  return (
    <main className={classes.page}>
      <header className={classes.siteHeader}>
        <Link to="/" className={classes.brandLink} aria-label="GameRec home">
          <BrandMark />
          <span>GameRec</span>
        </Link>
        <nav className={classes.siteNav} aria-label="Landing page navigation">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>
          <a href="#ai-picks">AI Picks</a>
        </nav>
        <Link to="/login" className={classes.signInLink}>Sign in</Link>
      </header>

      <section className={classes.hero} aria-labelledby="hero-title">
        <div className={classes.heroCopy}>
          <p className={classes.eyebrow}>A calmer way through a crowded library</p>
          <h1 id="hero-title">Turn your backlog into a playable roadmap.</h1>
          <p className={classes.heroSubheadline}>
            GameRec understands your taste, mood, and play history so you always know what to play next.
          </p>
          <div className={classes.heroActions}>
            <Link to="/register" className={classes.primaryCta}>
              Start building your library
              <IconArrowRight size={17} stroke={1.9} />
            </Link>
            <a href="#how-it-works" className={classes.secondaryCta}>See how it works</a>
          </div>
        </div>

        <div className={classes.heroVisual}>
          <img
            className={classes.heroArt}
            src={heroArt}
            alt="A stylized game discovery scene with game cards, a controller, a radar interface, ratings, player signals, and a journal."
            fetchPriority="high"
          />
        </div>
      </section>

      <section className={classes.problemSection} aria-labelledby="problem-title">
        <div>
          <p className={classes.sectionLabel}>Backlog fatigue</p>
          <h2 id="problem-title">Owning more games should not make choosing one harder.</h2>
        </div>
        <p>
          A full library can start to feel like homework: half-remembered saves, paused campaigns,
          wishlisted releases, and the quiet pressure to pick correctly. GameRec keeps the context
          around each game, so choosing feels considered instead of draining.
        </p>
      </section>

      <section id="features" className={classes.featuresSection} aria-labelledby="features-title">
        <div className={classes.sectionIntro}>
          <p className={classes.sectionLabel}>Library as memory</p>
          <h2 id="features-title">Everything you need to decide, without turning play into admin.</h2>
        </div>
        <div className={classes.featureGrid}>
          {features.map((feature) => (
            <article className={classes.featureItem} key={feature.title}>
              <FeatureIconStage feature={feature} />
              <div>
                <h3>{feature.title}</h3>
                <p>{feature.body}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section id="how-it-works" className={classes.howSection} aria-labelledby="how-title">
        <div className={classes.sectionIntro}>
          <p className={classes.sectionLabel}>How it works</p>
          <h2 id="how-title">Small actions become useful context.</h2>
        </div>
        <ol className={classes.stepList}>
          {steps.map((step, index) => (
            <li key={step}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <strong>{step}</strong>
            </li>
          ))}
        </ol>
      </section>

      <section id="ai-picks" className={classes.aiSection} aria-labelledby="ai-title">
        <div className={classes.aiCopy}>
          <p className={classes.sectionLabel}>AI Picks</p>
          <h2 id="ai-title">Recommendations with a reason you can recognize.</h2>
          <p>
            GameRec does not ask you to trust a black box. It shows the taste signals behind each
            suggestion: the moods you log, the games you finish, the genres you return to, and the
            time you realistically have.
          </p>
        </div>
        <div className={classes.aiShowcase}>
          <div className={classes.aiPosterStack} aria-hidden="true">
            {posterCards.slice(0, 3).map((poster) => (
              <PosterCard key={poster.title} {...poster} />
            ))}
          </div>
          <ReasonPanel />
        </div>
      </section>

      <section className={classes.finalCta} aria-labelledby="final-title">
        <IconListCheck size={22} stroke={1.8} aria-hidden="true" />
        <h2 id="final-title">Come back to the feeling, not the spreadsheet.</h2>
        <p>Your next game should feel chosen, remembered, and possible to finish.</p>
        <Link to="/register" className={classes.primaryCta}>
          Plan your next game
          <IconArrowRight size={17} stroke={1.9} />
        </Link>
      </section>

      <footer className={classes.footer}>
        <span><IconBook2 size={15} stroke={1.8} /> GameRec</span>
        <span>Personal game discovery and backlog planning.</span>
      </footer>
    </main>
  );
}
