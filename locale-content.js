/* Localized dynamic content that is shared by the API-driven renderers. */
(function(){
  const localeApi = window.PortfolioLocale;
  if(!localeApi) return;

  const PROJECT_COPY = {
    'regal-erkennung': {
      desc: 'Baden Hackt 2026 — a system that uses <b style="color:var(--acc)">YOLOv11n-cls</b> to recognize products on a shelf. When a product is removed, it automatically sends a reorder email with a CSV attachment.',
      stack: 'Python · FastAPI · YOLOv11n-cls · OpenCV · uvicorn',
    },
    portfolio: {
      desc: 'No template — the frontend talks to its own <b style="color:var(--acc)">FastAPI</b> backend: live GitHub stats, project metadata, an admin panel for editing content and uptime monitoring. Deployed on a self-managed Oracle Cloud VM.',
      stack: 'Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare',
    },
    'codex-claude-transfer': {
      desc: 'A local CLI tool (<b style="color:var(--acc)">cct</b>) that transfers Codex and Claude Code sessions between machines. Export, copy and import sessions as <code>.codexbundle</code> files — no cloud, account or server. Optional LAN sync.',
      stack: 'Go · Cobra · Indexed State · Local-Only',
    },
    'cli-agent': {
      desc: 'A CLI chatbot that uses function calling through the Google Gemini API. It can read and write files and run Python files in a restricted workspace — built as a learning project for the Boot.dev AI agent course.',
      stack: 'Python · Google GenAI SDK · Function Calling · uv',
    },
    'machine-learning': {
      desc: 'A machine-learning school project (LB-259): predicting California house prices as a regression problem. Data analysis, model training and evaluation in Jupyter notebooks with scikit-learn.',
      stack: 'Python · Jupyter · scikit-learn · Pandas',
    },
  };

  const OPEN_SOURCE_COPY = {
    'nushell/nushell': {title:'Parser scope leak fixed', desc:'Fixed scope loss during interpolation and added regression tests.'},
    'pygments/pygments': {title:'CSS color support extended', desc:'Added support and tests for transparent in styles and HTML output.'},
    'go-git/go-git': {title:'Gitignore API clarified', desc:'Documented paths, directories and match precedence more precisely.'},
    'lingui/js-lingui': {title:'Dynamic Next.js route extraction fixed', desc:'Fixed Lingui extraction for dynamic Next.js routes such as [slug] and [...params].'},
    'toml-rs/toml': {title:'TOML datetimes preserved', desc:'Preserved explicit TOML datetime values during deserialization without changing generic cross-format conversions.'},
  };

  const copyFields = (target, source, fields) => {
    if(!source) return target;
    const patch = {};
    fields.forEach(field => {
      if(typeof source[field] === 'string') patch[field] = source[field];
    });
    return {...target, ...patch};
  };

  function applyEditableEnglishCopy(result, raw){
    const translation = raw?.translations?.en;
    if(!translation) return result;

    result.hero = copyFields(result.hero || {}, translation.hero, ['name', 'lede']);
    if(Array.isArray(translation.hero?.phrases)) result.hero.phrases = translation.hero.phrases.slice();
    result.now = copyFields(result.now || {}, translation.now, ['status', 'detail']);

    if(Array.isArray(translation.about?.paragraphs)){
      result.about = {...(result.about || {}), paragraphs: translation.about.paragraphs.slice()};
    }
    if(Array.isArray(result.stats) && Array.isArray(translation.stats)){
      result.stats = result.stats.map((stat, index) =>
        copyFields(stat, translation.stats[index], ['label']),
      );
    }
    if(Array.isArray(result.skills) && Array.isArray(translation.skills)){
      result.skills = result.skills.map((skill, index) => {
        const translated = translation.skills[index];
        const next = copyFields(skill, translated, ['key']);
        return Array.isArray(translated?.items) ? {...next, items: translated.items.slice()} : next;
      });
    }
    if(Array.isArray(result.projects) && Array.isArray(translation.projects)){
      const bySlug = new Map(translation.projects.map(project => [project.slug, project]));
      result.projects = result.projects.map(project => {
        const translated = bySlug.get(project.slug);
        const next = copyFields(project, translated, ['title', 'desc', 'stack', 'content']);
        if(Array.isArray(translated?.badges)){
          next.badges = (next.badges || []).map((badge, index) =>
            copyFields(badge, translated.badges[index], ['label']),
          );
        }
        return next;
      });
    }
    if(Array.isArray(result.open_source) && Array.isArray(translation.open_source)){
      const byKey = new Map(translation.open_source.map(item => [`${item.repo}#${item.pr}`, item]));
      result.open_source = result.open_source.map(item =>
        copyFields(item, byKey.get(`${item.repo}#${item.pr}`), ['title', 'desc', 'tech']),
      );
    }
    if(Array.isArray(result.learning) && Array.isArray(translation.learning)){
      result.learning = result.learning.map((item, index) =>
        copyFields(item, translation.learning[index], ['kind', 'name', 'date', 'title']),
      );
    }
    return result;
  }
  const originalLocalizeContent = localeApi.localizeContent;
  localeApi.localizeContent = function(content, locale){
    const result = originalLocalizeContent(content, locale);
    if(locale !== 'en' || !result) return result;
    if(Array.isArray(result.projects)){
      result.projects = result.projects.map(project => {
        const translation = PROJECT_COPY[project.slug];
        return translation ? {...project, ...translation} : project;
      });
    }
    if(Array.isArray(result.open_source)){
      result.open_source = result.open_source.map(item => {
        const translation = OPEN_SOURCE_COPY[item.repo];
        return translation ? {...item, ...translation} : item;
      });
    }
    return locale === 'en' ? applyEditableEnglishCopy(result, content) : result;
  };
})();
