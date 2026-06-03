import {
  IconArrowRight,
  IconBook2,
  IconDeviceGamepad2,
  IconListCheck,
  IconNotebook,
  IconSparkles,
  IconStar,
} from '@tabler/icons-react';
import { Link } from 'react-router';
import classes from './LandingPage.module.css';

const posterCards = [
  { title: 'Ashen Gate', meta: 'Atmospheric adventure', tone: 'ember' },
  { title: 'Low Tide Signal', meta: 'Quiet exploration', tone: 'teal' },
  { title: 'Vesper Drift', meta: 'Story rich', tone: 'gold' },
  { title: 'Iron Orchard', meta: 'Tactical challenge', tone: 'blue' },
];

const queueItems = [
  { title: 'Ashen Gate', status: 'Tonight', note: '40 min session' },
  { title: 'Low Tide Signal', status: 'Weekend', note: 'Exploration mood' },
  { title: 'Iron Orchard', status: 'Later', note: 'Needs focus' },
];

const features = [
  {
    title: 'Taste-aware recommendations',
    body: 'See picks shaped by the games you finish, abandon, rate, save, and write about.',
    fragment: 'reason',
  },
  {
    title: 'Track your entire library',
    body: 'Keep playing, paused, wishlist, completed, and retired games in one calm view.',
    fragment: 'library',
  },
  {
    title: 'Plan your play queue',
    body: 'Turn vague intention into a short list that respects your time and current mood.',
    fragment: 'queue',
  },
  {
    title: 'Journal every play session',
    body: 'Capture why a game stayed with you, where you stopped, and what to return to next.',
    fragment: 'journal',
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

function LaptopMockup() {
  return (
    <div className={classes.laptopFrame} aria-label="GameRec recommendation dashboard preview">
      <div className={classes.laptopTopBar}>
        <span><BrandMark /> GameRec</span>
        <span className={classes.windowDots} aria-hidden="true"><i /><i /><i /></span>
      </div>
      <div className={classes.dashboardGrid}>
        <aside className={classes.mockNav} aria-label="Preview navigation">
          <span className={classes.mockNavActive}>Library</span>
          <span>Recommendations</span>
          <span>Play queue</span>
          <span>Journal</span>
        </aside>
        <section className={classes.mockMain} aria-label="Preview recommendation content">
          <div className={classes.mockHeader}>
            <p>Tonight's strongest pick</p>
            <h2>A playable roadmap for the mood you are in.</h2>
          </div>
          <div className={classes.heroPickGrid}>
            <div className={classes.featuredPoster} aria-hidden="true">
              <span>Ashen Gate</span>
            </div>
            <ReasonPanel compact />
          </div>
          <div className={classes.posterRail} aria-label="Preview library covers">
            {posterCards.map((poster) => (
              <PosterCard key={poster.title} {...poster} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function PhoneMockup() {
  return (
    <aside className={classes.phoneFrame} aria-label="GameRec mobile play queue preview">
      <div className={classes.phoneNotch} aria-hidden="true" />
      <div className={classes.phoneHeader}>
        <strong>Play Queue</strong>
        <span>3 ready</span>
      </div>
      <ol className={classes.phoneQueue}>
        {queueItems.map((item, index) => (
          <li key={item.title}>
            <span className={classes.queueNumber}>{index + 1}</span>
            <span>
              <strong>{item.title}</strong>
              <small>{item.note}</small>
            </span>
            <em>{item.status}</em>
          </li>
        ))}
      </ol>
      <div className={classes.journalPreview}>
        <span><IconNotebook size={14} stroke={1.9} /> Journal note</span>
        <p>Stopped after the tower shortcut. Next session: return before the storm area.</p>
      </div>
    </aside>
  );
}

function FeatureFragment({ type }: { type: string }) {
  if (type === 'reason') {
    return (
      <div className={classes.fragmentReason}>
        <span><IconStar size={13} /> Similar taste signal</span>
        <strong>Slow-burn mystery, short enough to finish</strong>
      </div>
    );
  }

  if (type === 'queue') {
    return (
      <div className={classes.fragmentQueue}>
        <span>Tonight</span>
        <span>Weekend</span>
        <span>Low focus</span>
      </div>
    );
  }

  if (type === 'journal') {
    return (
      <div className={classes.fragmentJournal}>
        <span>Session note</span>
        <p>Worth continuing because the world is opening up, not because it is next on the list.</p>
      </div>
    );
  }

  return (
    <div className={classes.fragmentLibrary}>
      <i />
      <i />
      <i />
      <i />
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
          <LaptopMockup />
          <PhoneMockup />
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
              <FeatureFragment type={feature.fragment} />
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
