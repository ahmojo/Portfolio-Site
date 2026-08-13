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
        desc: 'A hackathon prototype for small businesses. A webcam and <b style="color:var(--acc)">YOLOv11n-cls</b> check shelf positions. If a product is missing across repeated scans, the backend can send a reorder email with a CSV attachment.',
        stack: 'Python · FastAPI · YOLOv11n-cls · OpenCV · uvicorn',
        content: (
          '## Project\n'
          + 'My team built a shelf monitor for small businesses at Baden Hackt 2026. A webcam checks whether products are visible in configured shelf positions.\n\n'
          + '## Flow\n'
          + '- The browser selects the camera and defines the shelf positions.\n'
          + '- **YOLOv11n-cls** detects visible products.\n'
          + '- **FastAPI** processes scans and can send a reorder email with a CSV attachment.\n\n'
          + '## Status\n'
          + 'This is a hackathon prototype. Model weights and demo files are kept outside the repository because of their size.'
        ),
      },
      portfolio: {
        title: 'This portfolio',
        desc: 'My portfolio site with its own <b style="color:var(--acc)">FastAPI</b> backend. The backend serves content, GitHub data and status values. An admin area manages the text. Docker runs the app on an Oracle Cloud VM.',
        stack: 'Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare',
        content: (
          '## Structure\n'
          + 'The frontend loads page content and project data from a FastAPI API. The backend also provides GitHub and uptime data.\n\n'
          + '## Management\n'
          + 'A protected admin area edits the content. SQLite stores it on the VM.\n\n'
          + '## Hosting\n'
          + 'Docker runs the app on an Oracle Cloud VM. Cloudflare handles DNS, HTTPS and caching. The backend stores reduced analytics data and does not retain full IP addresses.'
        ),
      },
      'codex-claude-transfer': {
        title: 'Codex Claude Transfer',
        desc: '<b style="color:var(--acc)">cct</b> moves local Codex and Claude Code sessions between machines. It exports them as a <code>.codexbundle</code>, verifies the file and imports it at the destination. It needs no cloud service by default.',
        stack: 'Go · Cobra · Indexed State · Local-Only',
        content: (
          '## Purpose\n'
          + 'Codex and Claude Code store sessions on the local machine. `cct` packages a project\'s sessions so you can continue them on another computer.\n\n'
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
        desc: 'A learning project from the Boot.dev course. A Python program sends tasks to Gemini and provides four local tools. The agent can read, change and run Python files inside the example folder.',
        stack: 'Python · Google GenAI SDK · Function Calling · uv',
        content: (
          '## Purpose\n'
          + 'I used this Boot.dev project to practise function calling with the Gemini API. The terminal program gives the model four tools:\n'
          + '- list files and directories\n'
          + '- read file contents\n'
          + '- write or overwrite files\n'
          + '- run Python files with arguments\n\n'
          + 'The tools only access `./calculator`. `call_function.py` maps each model request to the matching Python function.\n\n'
          + '## Limitation\n'
          + 'The repository is a learning exercise, not a finished coding agent. Model-driven file changes and Python execution remain risky.'
        ),
      },
      'machine-learning': {
        title: 'Machine Learning',
        desc: 'A school project that predicts median house values in California. Three Jupyter notebooks cover data description, model training and evaluation with scikit-learn.',
        stack: 'Python · Jupyter · scikit-learn · Pandas',
        content: (
          '## Task\n'
          + 'A regression model predicts an area\'s median house value (`median_house_value`). Inputs include income, age, room count and location.\n\n'
          + '## Dataset\n'
          + 'The project uses the California Housing Prices dataset from StatLib and the 1990 California census. The rows describe areas and contain no names or contact details.\n\n'
          + '## Notebooks\n'
          + '- `data_description.ipynb` describes and checks the data.\n'
          + '- `model.ipynb` prepares the data and trains the model.\n'
          + '- `evaluation.ipynb` evaluates the predictions.'
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
