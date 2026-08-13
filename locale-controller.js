/* Public-page copy and interaction layer for the DE/EN switch. */
(function(){
  const localeApi = window.PortfolioLocale;
  if(!localeApi) return;

  const STATIC_COPY = [
    {selector:'.nav-links .nav-link:nth-child(1)', de:'über mich', en:'about'},
    {selector:'.nav-links .nav-link:nth-child(2)', de:'skills', en:'skills'},
    {selector:'.nav-links .nav-link:nth-child(3)', de:'projekte', en:'projects'},
    {selector:'.nav-links .nav-link:nth-child(4)', de:'open source', en:'open source'},
    {selector:'.nav-links .nav-link:nth-child(5)', de:'lernen', en:'learning'},
    {selector:'.nav-mob > a:nth-child(1)', de:'über mich', en:'about'},
    {selector:'.nav-mob > a:nth-child(2)', de:'skills', en:'skills'},
    {selector:'.nav-mob > a:nth-child(3)', de:'projekte', en:'projects'},
    {selector:'.nav-mob > a:nth-child(4)', de:'open source', en:'open source'},
    {selector:'.nav-mob > a:nth-child(5)', de:'lernen', en:'learning'},
    {selector:'.hero-lede', html:true, de:'<strong>IMS-Schüler mit Backend-Fokus</strong> aus der Schweiz. Ich baue am liebsten Dinge, die einfach zuverlässig laufen - mit Python, C# und JavaScript.', en:'<strong>IMS student focused on backend development</strong> from Switzerland. I like building things that simply run reliably — with Python, C# and JavaScript.'},
    {selector:'.hero-links a:nth-child(1)', html:true, de:'projekte ansehen <span class="arr">↓</span>', en:'view projects <span class="arr">↓</span>'},
    {selector:'#about .sec-num', html:true, de:'<b>01</b> &nbsp; über mich', en:'<b>01</b> &nbsp; about'},
    {selector:'#about .sec-title', de:'Wer ich bin', en:'Who I am'},
    {selector:'#about .about-text p:nth-child(1)', html:true, de:'Ich bin <strong>Ahmet</strong>, 18 Jahre alt, aus dem Aargau. Seit der Bezirksschule interessiere ich mich für Informatik - deshalb die <span class="hl">IMS</span>, aktuell im 3. Jahr.', en:'I\'m <strong>Ahmet</strong>, 18, from Aargau. I\'ve been interested in computer science since middle school — that\'s why I\'m studying at <span class="hl">IMS</span>, currently in my third year.'},
    {selector:'#about .about-text p:nth-child(2)', html:true, de:'Mein Schwerpunkt liegt auf <strong>Backend-Entwicklung</strong>. Daneben interessiert mich Cybersecurity - ich lerne, wie Systeme funktionieren und wie man sie sicherer macht.', en:'My focus is <strong>backend development</strong>. I\'m also interested in cybersecurity — learning how systems work and how to make them safer.'},
    {selector:'#about .about-text p:nth-child(3)', html:true, de:'Neben der Schule bilde ich mich selbständig weiter und lerne auch in meiner Freizeit gerne neue Informatik-Themen, zum Beispiel über Boot.dev. Im <span class="hl">Praktikum im 4. Jahr</span> möchte ich dieses Wissen an echten Aufgaben anwenden und weiter ausbauen.', en:'Alongside school, I keep learning independently and enjoy exploring new areas of computer science in my free time, for example through Boot.dev. During my <span class="hl">internship in year four</span>, I want to apply this knowledge to real-world tasks and keep building on it.'},
    {selector:'#about .stat-l:nth-child(1)', de:'Jahr · IMS', en:'3rd year · IMS'},
    {selector:'#about .stat-l:nth-child(2)', de:'Projekte', en:'projects'},
    {selector:'#about .stat-l:nth-child(3)', de:'Zertifikate · Boot.dev', en:'certificates · Boot.dev'},
    {selector:'#about .stat-l:nth-child(4)', de:'Hackathon', en:'hackathon'},
    {selector:'#skills .sec-num', html:true, de:'<b>02</b> &nbsp; skills', en:'<b>02</b> &nbsp; skills'},
    {selector:'#gh-panel .gh-panel-title', html:true, de:'<span class="dot"></span>GitHub-Aktivität <span id="gh-year" style="color:var(--ink-mute);font-weight:400"></span>', en:'<span class="dot"></span>GitHub activity <span id="gh-year" style="color:var(--ink-mute);font-weight:400"></span>'},
    {selector:'#gh-panel .gh-stat-l:nth-child(1)', de:'commits · Jahr', en:'commits · year'},
    {selector:'#gh-panel .gh-stat-l:nth-child(2)', de:'aktueller Streak', en:'current streak'},
    {selector:'#gh-panel .gh-stat-l:nth-child(3)', de:'längster Streak', en:'longest streak'},
    {selector:'#gh-panel .gh-stat-l:nth-child(4)', de:'öffentliche Repos', en:'public repos'},
    {selector:'#projects .sec-num', html:true, de:'<b>03</b> &nbsp; projekte', en:'<b>03</b> &nbsp; projects'},
    {selector:'#projects .sec-title', de:'Was ich gebaut habe', en:'Things I have built'},
    {selector:'.projs .proj:nth-child(1) .proj-title', de:'Regal-Erkennung für KMU', en:'Shelf recognition for SMEs'},
    {selector:'.projs .proj:nth-child(1) .proj-desc', html:true, de:'Hackathon-Prototyp für kleine Betriebe. Eine Webcam und <b style="color:var(--acc)">YOLOv11n-cls</b> prüfen Regalplätze. Fehlt ein Produkt bei mehreren Scans, kann das Backend eine Bestellmail mit CSV-Anhang senden.', en:'A hackathon prototype for small businesses. A webcam and <b style="color:var(--acc)">YOLOv11n-cls</b> check shelf positions. If a product is missing across repeated scans, the backend can send a reorder email with a CSV attachment.'},
    {selector:'.projs .proj:nth-child(1) .proj-stack', html:true, de:'<b>stack ·</b> Python · FastAPI · YOLOv11n-cls · OpenCV · uvicorn', en:'<b>stack ·</b> Python · FastAPI · YOLOv11n-cls · OpenCV · uvicorn'},
    {selector:'.projs .proj:nth-child(2) .proj-title', de:'Codex Claude Transfer', en:'Codex Claude Transfer'},
    {selector:'.projs .proj:nth-child(2) .proj-desc', html:true, de:'<b style="color:var(--acc)">cct</b> überträgt lokale Codex- und Claude-Code-Sitzungen zwischen Rechnern. Es exportiert sie als <code>.codexbundle</code>, prüft die Datei und importiert sie am Ziel. Standardmäßig braucht es keinen Cloud-Dienst.', en:'<b style="color:var(--acc)">cct</b> moves local Codex and Claude Code sessions between machines. It exports them as a <code>.codexbundle</code>, verifies the file and imports it at the destination. It needs no cloud service by default.'},
    {selector:'.projs .proj:nth-child(2) .proj-stack', html:true, de:'<b>stack ·</b> Go · Cobra · Indexed State · Local-Only', en:'<b>stack ·</b> Go · Cobra · Indexed State · Local-Only'},
    {selector:'.projs .proj:nth-child(3) .proj-title', de:'Dieses Portfolio', en:'This portfolio'},
    {selector:'.projs .proj:nth-child(3) .proj-desc', html:true, de:'Meine Portfolio-Seite mit eigenem <b style="color:var(--acc)">FastAPI</b>-Backend. Das Backend liefert Inhalte, GitHub-Daten und Statuswerte. Ein Admin-Bereich verwaltet die Texte. Die Anwendung läuft per Docker auf einer Oracle-Cloud-VM.', en:'My portfolio site with its own <b style="color:var(--acc)">FastAPI</b> backend. The backend serves content, GitHub data and status values. An admin area manages the text. Docker runs the app on an Oracle Cloud VM.'},
    {selector:'.projs .proj:nth-child(3) .proj-stack', html:true, de:'<b>stack ·</b> Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare', en:'<b>stack ·</b> Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare'},
    {selector:'.projs .proj:nth-child(4) .proj-title', de:'CLI-Agent mit Tool-Nutzung', en:'CLI agent with tool use'},
    {selector:'.projs .proj:nth-child(4) .proj-desc', html:true, de:'Lernprojekt aus dem Boot.dev-Kurs. Ein Python-Programm sendet Aufgaben an Gemini und stellt vier lokale Werkzeuge bereit. Der Agent kann Dateien im Beispielordner lesen, ändern und Python-Dateien ausführen.', en:'A learning project from the Boot.dev course. A Python program sends tasks to Gemini and provides four local tools. The agent can read, change and run Python files inside the example folder.'},
    {selector:'.projs .proj:nth-child(4) .proj-stack', html:true, de:'<b>stack ·</b> Python · Google GenAI SDK · Function Calling · uv', en:'<b>stack ·</b> Python · Google GenAI SDK · Function Calling · uv'},
    {selector:'.projs .proj:nth-child(5) .proj-title', de:'Machine Learning', en:'Machine learning'},
    {selector:'.projs .proj:nth-child(5) .proj-desc', de:'Schulprojekt zur Vorhersage mittlerer Hauswerte in Kalifornien. Drei Jupyter Notebooks behandeln Datenbeschreibung, Modelltraining und Auswertung mit scikit-learn.', en:'A school project that predicts median house values in California. Three Jupyter notebooks cover data description, model training and evaluation with scikit-learn.'},
    {selector:'.projs .proj:nth-child(5) .proj-stack', html:true, de:'<b>stack ·</b> Python · Jupyter · scikit-learn · Pandas', en:'<b>stack ·</b> Python · Jupyter · scikit-learn · Pandas'},
    {selector:'#opensource .sec-num', html:true, de:'<b>04</b> &nbsp; open source', en:'<b>04</b> &nbsp; open source'},
    {selector:'#opensource .sec-title', de:'Beiträge, die gemergt wurden', en:'Contributions that got merged'},
    {selector:'#opensource .oss-card:nth-child(1) .oss-title', de:'Parser-Scope-Leak behoben', en:'Parser scope leak fixed'},
    {selector:'#opensource .oss-card:nth-child(1) .oss-desc', de:'Scope-Verlust bei Interpolation behoben und Regressionstests ergänzt.', en:'Fixed scope loss during interpolation and added regression tests.'},
    {selector:'#opensource .oss-card:nth-child(2) .oss-title', de:'CSS-Farbe erweitert', en:'CSS color support extended'},
    {selector:'#opensource .oss-card:nth-child(2) .oss-desc', de:'transparent in Styles und HTML-Ausgabe unterstützt und getestet.', en:'Added support and tests for transparent in styles and HTML output.'},
    {selector:'#opensource .oss-card:nth-child(3) .oss-title', de:'Gitignore-API erklärt', en:'Gitignore API clarified'},
    {selector:'#opensource .oss-card:nth-child(3) .oss-desc', de:'Pfade, Verzeichnisse und Match-Priorität präziser dokumentiert.', en:'Documented paths, directories and match precedence more precisely.'},
    {selector:'#opensource .oss-card:nth-child(4) .oss-title', de:'Bugfix für dynamische Next.js-Routen', en:'Dynamic Next.js route extraction fixed'},
    {selector:'#opensource .oss-card:nth-child(4) .oss-desc', de:'Behebt die Lingui-Extraktion für dynamische Next.js-Routen wie [slug] oder [...params].', en:'Fixed Lingui extraction for dynamic Next.js routes such as [slug] and [...params].'},
    {selector:'#opensource .oss-card:nth-child(5) .oss-title', de:'TOML-Datetimes beibehalten', en:'TOML datetimes preserved'},
    {selector:'#opensource .oss-card:nth-child(5) .oss-desc', de:'Explizite TOML-Datetimes beim Deserialisieren beibehalten, ohne generische Cross-Format-Konvertierungen zu ändern.', en:'Preserved explicit TOML datetime values during deserialization without changing generic cross-format conversions.'},
    {selector:'#learning .sec-num', html:true, de:'<b>05</b> &nbsp; lernen', en:'<b>05</b> &nbsp; learning'},
    {selector:'#learning .sec-title', de:'Eigenständig weiterlernen', en:'Learning independently'},
    {selector:'.learn-summary', html:true, de:'<b>9 completions</b> - 6 courses · 3 projects · klick für Zertifikat', en:'<b>9 completions</b> - 6 courses · 3 projects · click for certificate'},
    {selector:'#feedback-content .feedback-kicker', de:'kurzes feedback', en:'quick feedback'},
    {selector:'#feedback-title', de:'Wie wirkt diese Portfolio-Seite auf dich?', en:'What do you think of this portfolio?'},
    {selector:'#feedback-content .feedback-intro', de:'Dein Eindruck?', en:'Your impression?'},
    {selector:'#feedback-comment-label', html:true, de:'Was könnte ich verbessern? <span>(optional)</span>', en:'What could I improve? <span>(optional)</span>'},
    {selector:'#feedback-comment', attr:'placeholder', de:'Ein Satz genügt.', en:'One sentence is enough.'},
    {selector:'.feedback-hint', de:"Maximal 1'000 Zeichen.", en:'Maximum 1,000 characters.'},
    {selector:'.feedback-submit', de:'Feedback senden', en:'Send feedback'},
    {selector:'#feedback-success .feedback-kicker', de:'feedback erhalten', en:'feedback received'},
    {selector:'.feedback-success-title', de:'Danke für dein Feedback.', en:'Thanks for your feedback.'},
    {selector:'footer .foot-meta a:nth-child(3)', de:'Impressum', en:'Legal notice'},
    {selector:'footer .foot-meta a:nth-child(4)', de:'Datenschutz', en:'Privacy'},
    {selector:'.foot-up', de:'↑ nach oben', en:'↑ back to top'},
    {selector:'#pv-prefix', de:'preview', en:'preview'},
  ];

  function applyStatic(locale){
    const copy = localeApi.UI[locale];
    STATIC_COPY.forEach(item => {
      document.querySelectorAll(item.selector).forEach(el => {
        const value = item[locale];
        if(item.attr) el.setAttribute(item.attr, value);
        else if(item.html) el.innerHTML = value;
        else el.textContent = value;
      });
    });

    document.documentElement.lang = locale;
    document.title = 'Ahmet Faruk Ilhan · Backend · IMS';
    const description = locale === 'en'
      ? 'Ahmet Faruk Ilhan — IMS student from Aargau focused on backend development with Python, C#, and FastAPI. Projects, Boot.dev certificates, and a self-managed backend stack.'
      : 'Ahmet Faruk Ilhan - IMS-Schüler aus dem Aargau mit Fokus auf Backend-Entwicklung (Python, C#, FastAPI). Projekte, Boot.dev-Zertifikate und ein eigener Backend-Stack. Deployed on a self-managed Oracle Cloud VM.';
    document.querySelector('meta[name="description"]')?.setAttribute('content', description);
    document.querySelector('meta[property="og:description"]')?.setAttribute('content', description);
    document.querySelector('meta[name="twitter:description"]')?.setAttribute('content', description);

    document.querySelectorAll('.locale-switch').forEach(button => {
      button.textContent = locale === 'de' ? 'EN' : 'DE';
      button.setAttribute('aria-label', copy.nav.switchTo);
      button.setAttribute('title', copy.nav.switchTo);
    });
    document.querySelector('.nav-logo')?.setAttribute('aria-label', copy.nav.home);
    document.querySelector('#nav-ham')?.setAttribute('aria-label', copy.nav.menu);
    if(window.__refreshFeedbackLocale) window.__refreshFeedbackLocale();
  }

  let locale = localeApi.get();
  window.__portfolioLocale = locale;
  window.__applyPortfolioLocale = function(next, updateUrl=true){
    locale = localeApi.set(next);
    window.__portfolioLocale = locale;
    applyStatic(locale);
    if(window.__SITE_CONTENT && window.__applyLocalizedContent){
      window.__applyLocalizedContent(window.__SITE_CONTENT);
    }
    if(window.__rerenderProjectMeta) window.__rerenderProjectMeta();
    if(updateUrl){
      try{
        const url = new URL(location.href);
        if(locale === 'de') url.searchParams.delete('lang');
        else url.searchParams.set('lang', locale);
        history.replaceState(null, '', url);
      }catch(_){ }
    }
  };

  document.querySelectorAll('.locale-switch').forEach(button => {
    button.addEventListener('click', () => {
      window.__applyPortfolioLocale(locale === 'de' ? 'en' : 'de');
      document.getElementById('nav-ham')?.classList.remove('open');
      document.getElementById('nav-mob')?.classList.remove('open');
    });
  });
  window.__applyPortfolioLocale(locale, false);
})();
