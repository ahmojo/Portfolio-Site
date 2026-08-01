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
        desc: 'Baden Hackt 2026 — a system that uses <b style="color:var(--acc)">YOLOv11n-cls</b> to recognize products on a shelf. When a product is removed, it automatically sends a reorder email with a CSV attachment.',
        stack: 'Python · FastAPI · YOLOv11n-cls · OpenCV · uvicorn',
        content: (
          '## The problem\n'
          + 'Small businesses often cannot afford professional shelf-monitoring systems. Empty shelves can go unnoticed until a customer points them out.\n\n'
          + '## Approach\n'
          + 'A webcam watches the shelf. A **YOLOv11n-cls** model classifies each shelf section as full or empty in every frame. When a product is removed, FastAPI automatically sends a reorder email with a CSV attachment — fully automated replenishment.\n\n'
          + '## What I learned\n'
          + '- Real-time inference is often about knowing *which frames not to infer on*.\n'
          + '- The real value appears where ML output becomes an ordinary business action: an email.\n\n'
          + '> Built in ~24h at **Baden Hackt 2026**.'
        ),
      },
      portfolio: {
        title: 'This portfolio',
        desc: 'No template — the frontend talks to its own <b style="color:var(--acc)">FastAPI</b> backend: live GitHub stats, project metadata, an admin panel for editing content and uptime monitoring. Deployed on a self-managed Oracle Cloud VM.',
        stack: 'Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare',
        content: (
          '## The idea\n'
          + 'Most portfolios are static. This one is a small full-stack project: the content, GitHub statistics and project metadata come from its own backend.\n\n'
          + '## Stack\n'
          + '- **FastAPI** serves content, GitHub stats, project metadata and uptime status.\n'
          + '- **SQLite** stores editable content; an admin panel updates it through the API.\n'
          + '- **Docker** runs on an **Oracle Cloud VM**, served behind **Cloudflare**.\n\n'
          + '## What I learned\n'
          + '- How to structure a FastAPI backend with routers, authentication and database access.\n'
          + '- HMAC-signed session cookies and rate limiting for the admin login.\n'
          + '- Deployment and operations: Docker, reverse proxy and monitoring.'
        ),
      },
      'codex-claude-transfer': {
        title: 'Codex Claude Transfer',
        desc: 'A local CLI tool (<b style="color:var(--acc)">cct</b>) that transfers Codex and Claude Code sessions between machines. Export, copy and import sessions as <code>.codexbundle</code> files — no cloud, account or server. Optional LAN sync.',
        stack: 'Go · Cobra · Indexed State · Local-Only',
        content: (
          '## The problem\n'
          + 'Anyone working with [Codex](https://github.com/openai/codex) or [Claude Code](https://github.com/anthropics/claude-code) on multiple machines needs a simple way to move sessions between them.\n\n'
          + '## Approach\n'
          + '`cct` is a small, entirely local CLI. Export a project\'s sessions into one `.codexbundle` file, copy it however you like (USB drive, `scp`, Syncthing or an encrypted disk), then import it on another machine. **No cloud, no account, no server** — and the agent\'s index/state stays untouched.\n\n'
          + '## Features\n'
          + '- Works with **Codex** *and* **Claude Code**, including cross-agent handoff\n'
          + '- Incremental sync: only new content is appended, nothing is overwritten\n'
          + '- Secret scan and redaction before export\n'
          + '- Optional bundle encryption\n'
          + '- Experimental LAN sync between explicitly paired devices\n\n'
          + '> Written in Go with [Cobra](https://github.com/spf13/cobra).'
        ),
      },
      'cli-agent': {
        title: 'CLI agent with tool use',
        desc: 'A CLI chatbot that uses function calling through the Google Gemini API. It can read and write files and run Python files in a restricted workspace — built as a learning project for the Boot.dev AI agent course.',
        stack: 'Python · Google GenAI SDK · Function Calling · uv',
        content: (
          '## The problem\n'
          + 'How does function calling actually work? How do you build an agent that calls tools on its own instead of only returning text?\n\n'
          + '## Approach\n'
          + 'A command-line program sends a prompt to Gemini and allows the model to call a small set of local tools:\n'
          + '- list files and directories\n'
          + '- read file contents\n'
          + '- write or overwrite files\n'
          + '- run Python files with arguments\n\n'
          + 'The tools are deliberately limited to `./calculator`, so the agent operates in a safe sandbox. The GenAI SDK registers the function declarations and dispatches model calls through `call_function.py`.\n\n'
          + '## What I learned\n'
          + '- How to structure a function-calling loop until a text response or iteration limit\n'
          + '- Why a restricted workspace is essential for safety\n\n'
          + '> Built during the [Boot.dev](https://www.boot.dev/) AI agent course.'
        ),
      },
      'machine-learning': {
        title: 'Machine Learning',
        desc: 'A machine-learning school project (LB-259): predicting California house prices as a regression problem. Data analysis, model training and evaluation in Jupyter notebooks with scikit-learn.',
        stack: 'Python · Jupyter · scikit-learn · Pandas',
        content: (
          '## Task\n'
          + 'Predict the median house value (`median_house_value`) from features such as income, age, room count and proximity to the ocean — a classic **regression problem**.\n\n'
          + '## Dataset\n'
          + 'California Housing Prices (StatLib / 1990 California census, CC0). It contains geographic, demographic and economic features for each area.\n\n'
          + '## Process\n'
          + '- **Data analysis** (`data_description.ipynb`): distributions, correlations and outliers\n'
          + '- **Model** (`model.ipynb`): training with scikit-learn\n'
          + '- **Evaluation** (`evaluation.ipynb`): metrics and error analysis\n\n'
          + '## What I learned\n'
          + '- How a complete ML project moves from raw data to evaluation\n'
          + '- The role feature selection and data preprocessing play\n\n'
          + '> School project, LB-259 — my first real contact with machine learning.'
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
