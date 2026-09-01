/* Small, dependency-free locale layer shared by the public portfolio pages. */
(function(){
  const STORAGE_KEY = 'portfolio-language';
  const valid = value => value === 'de' || value === 'en';

  const UI = {
    de: {
      nav: {
        about: 'über mich',
        skills: 'skills',
        projects: 'projekte',
        openSource: 'open source',
        learning: 'lernen',
        home: 'Zur Startseite',
        menu: 'Menü',
        switchTo: 'Auf Englisch wechseln',
        language: 'Sprache auswählen',
        useGerman: 'Deutsch verwenden',
        useEnglish: 'Englisch verwenden',
      },
      hero: { viewProjects: 'projekte ansehen' },
      sections: {
        about: 'über mich',
        who: 'Wer ich bin',
        skills: 'skills',
        projects: 'projekte',
        projectTitle: 'Was ich gebaut habe',
        openSource: 'open source',
        openSourceTitle: 'Beiträge, die gemergt wurden',
        learning: 'lernen',
        learningTitle: 'Eigenständig weiterlernen',
      },
      github: {
        seeStars: count => `${count} GitHub-Stars ansehen`,
        seeForks: count => `${count} GitHub-Forks ansehen`,
        openPull: (repo, pr) => `${repo} Pull Request ${pr} öffnen`,
        notFound: 'nicht gefunden',
        updated: value => `aktualisiert ${value}`,
        metrics: {
          releaseDownloadsLabel: 'Release-Downloads',
          releaseDownloadsTitle: 'Release-Downloads',
          releaseDownloadsNote: 'Plattform-Binaries aller Releases',
          trackedTotalLabel: 'Klone seit Aufzeichnung',
          trackedTotalTitle: 'Erfasste Klonvorgänge seit Beginn der Aufzeichnung',
          uniqueClonersLabel: 'Eindeutige Klon-Quellen',
          uniqueClonersTitle: 'Eindeutige Klon-Quellen in den letzten 14 Tagen',
          clones14dLabel: 'Klonvorgänge',
          clones14dTitle: 'Klonvorgänge in den letzten 14 Tagen',
          last14Days: 'letzte 14 Tage',
          since: value => `seit ${value}`,
          deltaLabel: value => `${value} gegenüber dem vorherigen Tagesstand`,
          metricAria: (label, value, delta, chart) => `${label}: ${value}${delta ? `, Veränderung ${delta}` : ''}${chart ? ', Verlauf öffnen' : ''}`,
          chartRangeLabel: 'Zeitraum des Verlaufs',
          range7: '7T',
          range30: '30T',
          rangeAll: 'Gesamt',
          chartAria: (label, points) => `${label}, Verlauf mit ${points} Tagesständen`,
          previousDailySnapshot: 'Vergleich mit dem vorherigen Tagesstand',
          helpLabel: 'Hinweise zu den Nutzungsmetriken',
          helpTitle: 'Zu diesen Metriken',
          closeHelp: 'Hinweise schließen',
          helpDownloads: 'Downloads zählen veröffentlichte Plattform-Binaries aller Versionen.',
          helpTraffic: 'Klonverkehr kann automatisierte Zugriffe durch CI, Scanner und andere Dienste enthalten.',
          helpUnique: 'Eindeutige Klon-Quellen und ihre Veränderung gelten nur für die letzten 14 Tage.',
        },
      },
      learning: {
        summary: 'klick für Zertifikat',
        project: 'Boot.dev project',
      },
      feedback: {
        kicker: 'kurzes feedback',
        title: 'Wie wirkt diese Portfolio-Seite auf dich?',
        intro: 'Dein Eindruck?',
        group: 'Portfolio bewerten',
        positiveAria: 'Daumen hoch: Portfolio gefällt mir',
        positive: 'Gefällt mir',
        negativeAria: 'Daumen runter: Portfolio gefällt mir noch nicht',
        negative: 'Noch nicht',
        comment: 'Was könnte ich verbessern?',
        optional: '(optional)',
        placeholder: 'Ein Satz genügt.',
        source: 'Wo hast du dieses Portfolio entdeckt?',
        max: "Maximal 1'000 Zeichen.",
        submit: 'Feedback senden',
        submitting: 'wird gesendet …',
        successKicker: 'feedback erhalten',
        success: 'Danke für dein Feedback.',
        rateLimit: 'In kurzer Zeit sind bereits mehrere Rückmeldungen eingegangen. Versuch es bitte später noch einmal.',
        unavailable: 'Das Feedback ist gerade nicht erreichbar. Versuch es bitte später noch einmal.',
        tooLong: "Bitte kürze den Kommentar auf maximal 1'000 Zeichen.",
        failed: 'Das Feedback konnte nicht gesendet werden. Versuch es bitte später noch einmal.',
      },
      footer: {
        legal: 'Impressum',
        privacy: 'Datenschutz',
        top: '↑ nach oben',
      },
      modal: { preview: 'preview', close: 'close', empty: title => `Vorschau für ${title} folgt in Kürze.`, code: 'Der Code liegt auf GitHub.' },
      project: {
        back: '← zurück zum Portfolio',
        loading: 'Projekt wird geladen …',
        noWriteup: 'Für dieses Projekt gibt es noch keinen Write-up.',
        checkRepo: 'Repository ansehen',
        noProject: slug => `Kein Projekt mit dem Slug ${slug}`,
      },
    },
    en: {
      nav: {
        about: 'about',
        skills: 'skills',
        projects: 'projects',
        openSource: 'open source',
        learning: 'learning',
        home: 'Back to home',
        menu: 'Menu',
        switchTo: 'Switch to German',
        language: 'Choose language',
        useGerman: 'Use German',
        useEnglish: 'Use English',
      },
      hero: { viewProjects: 'view projects' },
      sections: {
        about: 'about',
        who: 'Who I am',
        skills: 'skills',
        projects: 'projects',
        projectTitle: 'Things I have built',
        openSource: 'open source',
        openSourceTitle: 'Contributions that got merged',
        learning: 'learning',
        learningTitle: 'Learning independently',
      },
      github: {
        seeStars: count => `See ${count} GitHub stars`,
        seeForks: count => `See ${count} GitHub forks`,
        openPull: (repo, pr) => `Open ${repo} pull request ${pr}`,
        notFound: 'not found',
        updated: value => `updated ${value}`,
        metrics: {
          releaseDownloadsLabel: 'Release downloads',
          releaseDownloadsTitle: 'Release downloads',
          releaseDownloadsNote: 'Platform binaries across all releases',
          trackedTotalLabel: 'Clones since tracking',
          trackedTotalTitle: 'Clone operations recorded since tracking began',
          uniqueClonersLabel: 'Unique clone sources',
          uniqueClonersTitle: 'Unique clone sources in the last 14 days',
          clones14dLabel: 'Clone operations',
          clones14dTitle: 'Clone operations in the last 14 days',
          last14Days: 'last 14 days',
          since: value => `since ${value}`,
          deltaLabel: value => `${value} compared with the previous daily snapshot`,
          metricAria: (label, value, delta, chart) => `${label}: ${value}${delta ? `, change ${delta}` : ''}${chart ? ', open history' : ''}`,
          chartRangeLabel: 'Chart time range',
          range7: '7d',
          range30: '30d',
          rangeAll: 'All',
          chartAria: (label, points) => `${label}, history with ${points} daily snapshots`,
          previousDailySnapshot: 'Compared with the previous daily snapshot',
          helpLabel: 'About these usage metrics',
          helpTitle: 'About these metrics',
          closeHelp: 'Close metric information',
          helpDownloads: 'Downloads count published platform binaries across all versions.',
          helpTraffic: 'Clone traffic may include automated access from CI systems, scanners, and other services.',
          helpUnique: 'Unique clone sources and their change apply only to the last 14 days.',
        },
      },
      learning: {
        summary: 'click for certificate',
        project: 'Boot.dev project',
      },
      feedback: {
        kicker: 'quick feedback',
        title: 'What do you think of this portfolio?',
        intro: 'Your impression?',
        group: 'Rate the portfolio',
        positiveAria: 'Thumbs up: I like this portfolio',
        positive: 'I like it',
        negativeAria: 'Thumbs down: this portfolio needs work',
        negative: 'Not quite',
        comment: 'What could I improve?',
        optional: '(optional)',
        placeholder: 'One sentence is enough.',
        source: 'Where did you discover this portfolio?',
        max: 'Maximum 1,000 characters.',
        submit: 'Send feedback',
        submitting: 'sending …',
        successKicker: 'feedback received',
        success: 'Thanks for your feedback.',
        rateLimit: 'Several feedback submissions were received in a short time. Please try again later.',
        unavailable: 'Feedback is currently unavailable. Please try again later.',
        tooLong: 'Please shorten the comment to a maximum of 1,000 characters.',
        failed: 'Your feedback could not be sent. Please try again later.',
      },
      footer: {
        legal: 'Legal notice',
        privacy: 'Privacy',
        top: '↑ back to top',
      },
      modal: { preview: 'preview', close: 'close', empty: title => `A preview for ${title} is coming soon.`, code: 'The code is on GitHub.' },
      project: {
        back: '← back to portfolio',
        loading: 'loading project …',
        noWriteup: 'No write-up is available for this project yet.',
        checkRepo: 'check the repository',
        noProject: slug => `no project with slug ${slug}`,
      },
    },
  };

  const EN_CONTENT = {
    hero: {
      lede: '<strong>IMS student focused on backend development</strong> from Switzerland. I like building things that simply run reliably — with Python, C# and JavaScript.',
      phrases: ['Backend · Python · C# · JavaScript', 'building things that should just run.'],
    },
    about: {
      paragraphs: [
        'I\'m <strong>Ahmet</strong>, 18, from Aargau. I\'ve been interested in computer science since middle school — that\'s why I\'m studying at <span class="hl">IMS</span>, currently in my third year.',
        'My focus is <strong>backend development</strong>. I\'m also interested in cybersecurity — learning how systems work and how to make them safer.',
        'Alongside school, I keep learning independently and enjoy exploring new areas of computer science in my free time, for example through Boot.dev. During my <span class="hl">internship in year four</span>, I want to apply this knowledge to real-world tasks and keep building on it.',
      ],
    },
    stats: [
      {label: '3rd year · IMS'},
      {label: 'projects'},
      {label: 'certificates · Boot.dev'},
      {label: 'hackathon'},
    ],
    projects: {
      'regal-erkennung': {
        title: 'Shelf recognition for SMEs',
        desc: 'A hackathon prototype for small businesses. A webcam checks configured shelf positions with <b style="color:var(--acc)">YOLOv11n-cls</b>. If a product is missing across repeated scans, FastAPI can send a reorder email with a CSV attachment.',
        stack: 'Python · FastAPI · YOLOv11n-cls · OpenCV · uvicorn',
        content: (
          '## Problem\n'
          + 'Empty shelf positions are easy to miss. The prototype detects missing products across repeated camera scans and can trigger a reorder.\n\n'
          + '## Architecture\n'
          + 'The browser selects the camera and shelf positions. **YOLOv11n-cls** classifies visible products. **FastAPI** processes scans and can send a reorder email with a CSV attachment.\n\n'
          + '## Status\n'
          + 'Hackathon prototype. Model weights and demo files stay outside the repository because of their size.'
        ),
      },
      portfolio: {
        title: 'This portfolio',
        desc: 'My portfolio site with its own <b style="color:var(--acc)">FastAPI</b> backend. The backend serves content, GitHub data and status values. A protected admin area manages the text. Docker runs the app on an Oracle Cloud VM.',
        stack: 'Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare',
        content: (
          '## Architecture\n'
          + 'The frontend and admin panel use the FastAPI API on the same origin. The backend serves static files, editable content, project data, and GitHub and uptime status. SQLite stores content and reduced analytics data.\n\n'
          + '## Usage\n'
          + 'The protected admin area edits the hero, about section, skills, and projects. The public page loads this data through `/api/content`.\n\n'
          + '## Hosting\n'
          + 'Docker Compose runs on an Oracle Cloud VM. Cloudflare handles DNS, HTTPS, and the CDN. The backend does not retain full IP addresses.'
        ),
      },
      'codex-claude-transfer': {
        title: 'Codex Claude Transfer',
        desc: '<b style="color:var(--acc)">cct</b> moves local Codex and Claude Code sessions between machines. It packages them as a <code>.codexbundle</code>, verifies the checksum and imports them at the destination. It needs no cloud service by default.',
        stack: 'Go · Cobra · Indexed State · Local-Only',
        content: (
          '## Problem\n'
          + 'Codex and Claude Code keep sessions locally. When you change machines or agents, you still need a simple way to carry the project context with you.\n\n'
          + '## Architecture\n'
          + '`cct` reads local session files, packages them into a `.codexbundle`, and verifies the bundle before import. It does not write to the agents\' index databases; they rescan imported files.\n\n'
          + '## Usage\n'
          + '```\n'
          + 'cct export --project .\n'
          + 'cct import ./project.codexbundle --dry-run\n'
          + 'cct import ./project.codexbundle\n'
          + '```\n\n'
          + '## Features\n'
          + '- Export and import for Codex and Claude Code\n'
          + '- Handoff between both agents\n'
          + '- CLI, terminal wizard and local browser app\n'
          + '- Secret scanning, optional encryption and LAN sync\n\n'
          + '## Note\n'
          + 'Bundles can contain prompts, code and credentials. Treat them as private work data.'
        ),
      },
      'cli-agent': {
        title: 'CLI agent with tool use',
        desc: 'A learning project from the Boot.dev course. A Python program sends tasks to Gemini and provides four local tools. The agent only works in `./calculator`, where it can read, change and run Python files.',
        stack: 'Python · Google GenAI SDK · Function Calling · uv',
        content: (
          '## Architecture\n'
          + 'The terminal program sends requests to Gemini through the Google GenAI SDK. Function calling selects one of four local tools; `call_function.py` dispatches each request to the matching Python function. The tools only work in `./calculator`.\n\n'
          + '## Usage\n'
          + 'The program can:\n'
          + '- list files and directories\n'
          + '- read file contents\n'
          + '- write or overwrite files\n'
          + '- run Python files with arguments\n\n'
          + '## Status\n'
          + 'The repository is a Boot.dev learning project, not a finished coding agent. Model-driven file changes and Python execution remain risky.'
        ),
      },
      'machine-learning': {
        title: 'Machine Learning',
        desc: 'A school project that predicts median house values in California. Three Jupyter notebooks document data checks, model training, and evaluation with scikit-learn.',
        stack: 'Python · Jupyter · scikit-learn · Pandas',
        content: (
          '## Architecture\n'
          + 'The workflow goes from the California Housing dataset through data checks and model training to evaluation. Three Jupyter notebooks cover those steps.\n\n'
          + '## Project\n'
          + 'A regression model predicts an area\'s median house value (`median_house_value`). Inputs include income, house age, room count, and location.\n\n'
          + '## Dataset\n'
          + 'The project uses the California Housing Prices dataset from StatLib and the 1990 California census. The rows describe areas and contain no names or contact details.\n\n'
          + '## Status\n'
          + 'School project. The notebooks document the learning and evaluation process.'
        ),
      },
    },
    openSource: {
      'nushell/nushell': {title: 'Parser scope leak fixed', desc: 'Fixed scope loss during interpolation and added regression tests.', tech: 'Rust · Parser'},
      'pygments/pygments': {title: 'CSS color support extended', desc: 'Added support and tests for transparent in styles and HTML output.', tech: 'Python · pytest'},
      'go-git/go-git': {title: 'Gitignore API clarified', desc: 'Documented paths, directories and match precedence more precisely.', tech: 'Go · API Docs'},
      'lingui/js-lingui': {title: 'Dynamic Next.js route extraction fixed', desc: 'Fixed Lingui extraction for dynamic Next.js routes such as [slug] and [...params].', tech: 'TypeScript'},
      'toml-rs/toml': {title: 'TOML datetimes preserved', desc: 'Preserved explicit TOML datetime values during deserialization without changing generic cross-format conversions.', tech: 'Rust · TOML'},
    },
  };

  const DE_DEFAULTS = {
    heroLede: '<strong>IMS-Schüler mit Backend-Fokus</strong> aus der Schweiz. Ich baue am liebsten Dinge, die einfach zuverlässig laufen - mit Python, C# und JavaScript.',
    about: [
      'Ich bin <strong>Ahmet</strong>, 18 Jahre alt, aus dem Aargau. Seit der Bezirksschule interessiere ich mich für Informatik - deshalb die <span class="hl">IMS</span>, aktuell im 3. Jahr.',
      'Mein Schwerpunkt liegt auf <strong>Backend-Entwicklung</strong>. Daneben interessiert mich Cybersecurity - ich lerne, wie Systeme funktionieren und wie man sie sicherer macht.',
      'Neben der Schule bilde ich mich selbständig weiter und lerne auch in meiner Freizeit gerne neue Informatik-Themen, zum Beispiel über Boot.dev. Im <span class="hl">Praktikum im 4. Jahr</span> möchte ich dieses Wissen an echten Aufgaben anwenden und weiter ausbauen.',
    ],
  };

  function clone(value){
    return value == null ? value : JSON.parse(JSON.stringify(value));
  }

  function useTranslation(current, original, translated){
    return !current || current === original ? translated : current;
  }

  function localizeContent(content, locale){
    if(locale !== 'en' || !content) return content;
    const result = clone(content);
    result.hero = result.hero || {};
    result.hero.lede = useTranslation(result.hero.lede, DE_DEFAULTS.heroLede, EN_CONTENT.hero.lede);
    result.hero.phrases = result.hero.phrases && result.hero.phrases.length
      ? result.hero.phrases.map((phrase, index) => useTranslation(
          phrase,
          index === 0 ? 'Backend · Python · C# · JavaScript' : 'building things that should just run.',
          EN_CONTENT.hero.phrases[index] || phrase,
        ))
      : EN_CONTENT.hero.phrases.slice();

    if(result.about && Array.isArray(result.about.paragraphs)){
      result.about.paragraphs = result.about.paragraphs.map((paragraph, index) =>
        useTranslation(paragraph, DE_DEFAULTS.about[index], EN_CONTENT.about.paragraphs[index] || paragraph),
      );
    }
    if(Array.isArray(result.stats)){
      result.stats = result.stats.map((stat, index) => ({
        ...stat,
        label: useTranslation(stat.label, ['Jahr · IMS', 'Projekte', 'Zertifikate · Boot.dev', 'Hackathon'][index], EN_CONTENT.stats[index]?.label || stat.label),
      }));
    }
    if(Array.isArray(result.projects)){
      result.projects = result.projects.map((project, index) => {
        const key = project.slug || Object.keys(EN_CONTENT.projects)[index];
        const translated = EN_CONTENT.projects[key];
        if(!translated) return project;
        return {
          ...project,
          title: useTranslation(project.title, ['Regal-Erkennung für KMU', 'Codex Claude Transfer', 'Dieses Portfolio', 'CLI-Agent mit Tool-Nutzung', 'Machine Learning'][index], translated.title),
          desc: useTranslation(project.desc, null, translated.desc),
          stack: useTranslation(project.stack, null, translated.stack),
          content: useTranslation(project.content, null, translated.content),
        };
      });
    }
    if(Array.isArray(result.open_source)){
      result.open_source = result.open_source.map(item => {
        const translated = EN_CONTENT.openSource[item.repo];
        return translated ? {
          ...item,
          title: useTranslation(item.title, null, translated.title),
          desc: useTranslation(item.desc, null, translated.desc),
          tech: useTranslation(item.tech, null, translated.tech),
        } : item;
      });
    }
    return result;
  }

  function localizeProject(project, locale){
    if(locale !== 'en' || !project) return project;
    if(project._localized === 'en'){
      const result = {...project};
      delete result._localized;
      return result;
    }
    const translated = EN_CONTENT.projects[project.slug];
    return translated ? {...project, ...translated} : project;
  }

  function get(){
    let fromQuery = '';
    try{ fromQuery = new URLSearchParams(location.search).get('lang') || ''; }catch(_){ }
    if(valid(fromQuery)) return fromQuery;
    try{
      const stored = localStorage.getItem(STORAGE_KEY);
      if(valid(stored)) return stored;
    }catch(_){ }
    return 'de';
  }

  function set(locale){
    const next = valid(locale) ? locale : 'de';
    try{ localStorage.setItem(STORAGE_KEY, next); }catch(_){ }
    return next;
  }

  window.PortfolioLocale = {
    UI,
    get,
    set,
    localizeContent,
    localizeProject,
    isValid: valid,
  };
})();
