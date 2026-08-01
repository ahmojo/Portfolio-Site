/* Faithful DE/EN copy switch for the legal pages. */
(function(){
  const localeApi = window.PortfolioLocale;
  if(!localeApi) return;

  const entry = (selector, de, en, html=false) => ({selector, de, en, html});
  const IMPRESSUM = [
    entry('.back', 'zurück zur Startseite', 'back to home'),
    entry('.sec-num', '<b>01</b> &nbsp; impressum', '<b>01</b> &nbsp; legal notice', true),
    entry('h1', 'Impressum', 'Legal notice'),
    entry('section:nth-of-type(1) h2', 'Verantwortlich für den Inhalt', 'Responsible for the content'),
    entry('section:nth-of-type(1) p:nth-of-type(2)', 'Aargau, Schweiz', 'Aargau, Switzerland'),
    entry('section:nth-of-type(1) p:nth-of-type(3)', 'E-Mail: <a href="mailto:ahmetfarukilhan@proton.me">ahmetfarukilhan@proton.me</a>', 'Email: <a href="mailto:ahmetfarukilhan@proton.me">ahmetfarukilhan@proton.me</a>', true),
    entry('section:nth-of-type(2) h2', 'Hinweis zur Adresse', 'Address notice'),
    entry('section:nth-of-type(2) p:nth-of-type(1)', 'Diese Website ist ein persönliches Portfolio. Aus Gründen des Persönlichkeitsschutzes wird keine private Wohnadresse öffentlich auf der Website veröffentlicht. Für berechtigte Anfragen ist eine Kontaktaufnahme per E-Mail möglich.', 'This website is a personal portfolio. To protect personal privacy, no private residential address is published on the website. Legitimate enquiries can be made by email.'),
    entry('section:nth-of-type(3) h2', 'Haftung für Inhalte und Links', 'Liability for content and links'),
    entry('section:nth-of-type(3) p:nth-of-type(1)', 'Die Inhalte dieser Website wurden sorgfältig erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte kann jedoch keine Gewähr übernommen werden. Diese Website enthält Links zu externen Websites, auf deren Inhalte kein Einfluss besteht.', 'The content of this website has been prepared with care. However, no guarantee can be given for its accuracy, completeness or timeliness. This website contains links to external websites whose content is outside our control.'),
    entry('section:nth-of-type(4) h2', 'Datenschutz', 'Privacy'),
    entry('section:nth-of-type(4) p:nth-of-type(1)', 'Informationen zur Verarbeitung personenbezogener Daten stehen in der <a href="datenschutz.html">Datenschutzerklärung</a>.', 'Information about the processing of personal data is available in the <a href="datenschutz.html">privacy policy</a>.', true),
    entry('footer', 'Stand: Mai 2026', 'Last updated: May 2026'),
  ];

  const PRIVACY = [
    entry('.back', 'zurück zur Startseite', 'back to home'),
    entry('.sec-num', '<b>01</b> &nbsp; datenschutz', '<b>01</b> &nbsp; privacy', true),
    entry('h1', 'Datenschutzerklärung', 'Privacy policy'),
    entry('section:nth-of-type(1) h2', 'Hosting und Schutz über Cloudflare', 'Hosting and protection through Cloudflare'),
    entry('section:nth-of-type(1) p:nth-of-type(1)', 'Diese Website wird über Cloudflare bereitgestellt und geschützt. Cloudflare dient als Content Delivery Network (CDN) und Sicherheitsdienst. Dabei können insbesondere IP-Adresse, Datum und Uhrzeit, angeforderte Dateien, Browser- und Verbindungsinformationen, Herkunftsland, Statuscodes sowie ähnliche technische Daten verarbeitet werden.', 'This website is provided and protected through Cloudflare. Cloudflare acts as a content delivery network (CDN) and security service. In particular, the IP address, date and time, requested files, browser and connection information, country of origin, status codes and similar technical data may be processed.'),
    entry('section:nth-of-type(1) p:nth-of-type(2)', 'Die Verarbeitung dient der sicheren und zuverlässigen Bereitstellung, der Abwehr missbräuchlicher Zugriffe, der Fehleranalyse und der technischen Überwachung der Website.', 'This processing is used to provide the website securely and reliably, prevent abusive access, analyze errors and monitor the website technically.'),
    entry('section:nth-of-type(1) p:nth-of-type(3)', 'Anbieter: Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA. Weitere Informationen stehen in der <a href="https://www.cloudflare.com/policies/privacy/" target="_blank" rel="noopener">Datenschutzerklärung von Cloudflare</a>.', 'Provider: Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA. More information is available in <a href="https://www.cloudflare.com/policies/privacy/" target="_blank" rel="noopener">Cloudflare\'s privacy policy</a>.', true),
    entry('section:nth-of-type(2) h2', 'Konservative Besucheranalyse', 'Conservative visitor analytics'),
    entry('section:nth-of-type(2) p:nth-of-type(1)', 'Die Website zählt nicht bereits den Seitenabruf. Ein Aufruf kann erst nach sichtbarer Nutzung der Seite und einer erfolgreichen Browserbestätigung als Seitenaufruf gespeichert werden. Besucher mit aktiviertem Do Not Track oder Global Privacy Control werden nicht in diese Analyse aufgenommen.', 'The website does not count a page request immediately. A visit is stored as a page view only after visible use of the page and successful browser verification. Visitors with Do Not Track or Global Privacy Control enabled are not included in this analysis.'),
    entry('section:nth-of-type(2) p:nth-of-type(2)', 'Gespeichert werden nur der aufgerufene Seitenpfad, Datum und Uhrzeit, der Hostname des Referrers, die Bestätigungsmethode und ein nicht rückrechenbarer Besucher-Hash, der täglich wechselt. Rohe IP-Adressen, vollständige Referrer-URLs und User-Agent-Strings werden nicht in der Besucherstatistik gespeichert. Wiederholte Bestätigungen derselben Seite und desselben Besucher-Tags werden nur einmal gezählt. Die Daten werden spätestens nach 90 Tagen gelöscht.', 'Only the page path, date and time, the referrer hostname, the verification method and a non-reversible visitor hash that changes daily are stored. Raw IP addresses, complete referrer URLs and User-Agent strings are not stored in the visitor statistics. Repeated confirmations for the same page and visitor tag are counted only once. The data is deleted after 90 days at the latest.'),
    entry('section:nth-of-type(2) p:nth-of-type(3)', 'Abgelehnte Zugriffe werden nicht als einzelne Datensätze gespeichert. Stattdessen werden ausschliesslich anonyme Tageszähler geführt, zum Beispiel für bekannte Bots, fehlende Browserbestätigungen, ungültige Seeds, fehlgeschlagene Turnstile-Prüfungen oder Rate-Limits.', 'Rejected requests are not stored as individual records. Instead, only anonymous daily counters are kept, for example for known bots, missing browser confirmations, invalid seeds, failed Turnstile checks or rate limits.'),
    entry('section:nth-of-type(3) h2', 'Cloudflare Turnstile', 'Cloudflare Turnstile'),
    entry('section:nth-of-type(3) p:nth-of-type(1)', 'Zur Unterscheidung plausibler Browsernutzung von automatisierten Zugriffen verwendet die Website Cloudflare Turnstile im verwalteten Modus. Das Turnstile-Skript wird erst nach sichtbarer Nutzung der Seite geladen. Es wertet technische Signale des Browsers und der Netzwerkverbindung aus und erzeugt einen kurzlebigen, einmal verwendbaren Bestätigungstoken.', 'To distinguish plausible browser use from automated access, the website uses Cloudflare Turnstile in managed mode. The Turnstile script is loaded only after visible use of the page. It evaluates technical signals from the browser and network connection and creates a short-lived, single-use confirmation token.'),
    entry('section:nth-of-type(3) p:nth-of-type(2)', 'Der Token und die aktuelle IP-Adresse werden vom Backend an die Siteverify-Schnittstelle von Cloudflare übermittelt. Das Backend prüft zusätzlich den erwarteten Hostnamen und die Aktion <code>portfolio_analytics</code>. Turnstile-Tokens und IP-Adressen werden nicht in den gespeicherten Besucherzeilen abgelegt.', 'The token and current IP address are sent by the backend to Cloudflare\'s Siteverify endpoint. The backend also checks the expected hostname and the <code>portfolio_analytics</code> action. Turnstile tokens and IP addresses are not stored in the saved visitor rows.', true),
    entry('section:nth-of-type(3) p:nth-of-type(3)', 'Informationen zur Verarbeitung durch Turnstile enthält das <a href="https://www.cloudflare.com/policies/privacy/" target="_blank" rel="noopener">Turnstile Privacy Addendum in der Cloudflare-Datenschutzerklärung</a>.', 'Information about processing through Turnstile is available in the <a href="https://www.cloudflare.com/policies/privacy/" target="_blank" rel="noopener">Turnstile Privacy Addendum in Cloudflare\'s privacy policy</a>.', true),
    entry('section:nth-of-type(4) h2', 'Technisch notwendige Cookies', 'Technically necessary cookies'),
    entry('section:nth-of-type(4) p:nth-of-type(1)', 'Für die Bestätigung werden ausschliesslich First-Party-Sicherheitscookies verwendet: ein signierter Analytics-Seed mit maximal fünf Minuten Laufzeit und, nach erfolgreicher Turnstile-Prüfung, eine an den täglichen Besucher-Hash gebundene Bestätigung bis zum Tagesende. Beide Cookies sind <code>HttpOnly</code>, in Produktion <code>Secure</code> und <code>SameSite=Lax</code>. Sie werden nicht für Werbung oder seitenübergreifendes Tracking verwendet.', 'The confirmation uses only first-party security cookies: a signed analytics seed with a maximum lifetime of five minutes and, after successful Turnstile verification, a confirmation bound to the daily visitor hash until the end of the day. Both cookies are <code>HttpOnly</code>, <code>Secure</code> in production and <code>SameSite=Lax</code>. They are not used for advertising or cross-site tracking.', true),
    entry('section:nth-of-type(5) h2', 'Weitere Dienste', 'Other services'),
    entry('section:nth-of-type(5) p:nth-of-type(1)', 'Die Domain wird über Infomaniak Network SA, Rue Eugène-Marziano 25, 1227 Les Acacias, Schweiz, verwaltet.', 'The domain is managed by Infomaniak Network SA, Rue Eugène-Marziano 25, 1227 Les Acacias, Switzerland.'),
    entry('section:nth-of-type(5) p:nth-of-type(2)', 'Schriftarten werden von Google Fonts eingebunden. Beim Laden kann der Browser technische Verbindungsdaten an Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland, übermitteln.', 'Fonts are loaded from Google Fonts. When they are loaded, the browser may transmit technical connection data to Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Ireland.'),
    entry('section:nth-of-type(6) h2', 'Kontakt- und Formulardaten', 'Contact and form data'),
    entry('section:nth-of-type(6) p:nth-of-type(1)', 'Angaben aus Kontakt- oder Administrationsfunktionen werden nur für den jeweiligen Zweck und zum Schutz vor Missbrauch verarbeitet. Sie werden nicht für Werbung verwendet und nur so lange gespeichert, wie es für den jeweiligen Zweck erforderlich ist.', 'Information submitted through contact or administration functions is processed only for the relevant purpose and to prevent misuse. It is not used for advertising and is stored only for as long as necessary for that purpose.'),
    entry('section:nth-of-type(7) h2', 'Privates Feedback', 'Private feedback'),
    entry('section:nth-of-type(7) p:nth-of-type(1)', 'Am Ende der Startseite kann freiwillig eine positive oder negative Bewertung abgegeben werden. Optional kann ein Kommentar mit maximal 1\'000 Zeichen ergänzt werden. Gespeichert werden nur die Bewertung, der Kommentar als reiner Text und der Zeitpunkt der Einsendung in UTC. Eine Auswahl vorgegebener Gründe wird nicht erfasst.', 'At the end of the home page, visitors can optionally submit a positive or negative rating. An optional comment of up to 1,000 characters can be added. Only the rating, the comment as plain text and the submission time in UTC are stored. No predefined reason choices are collected.'),
    entry('section:nth-of-type(7) p:nth-of-type(2)', 'Das Feedback dient ausschliesslich der internen Verbesserung dieser Website. Es wird nicht öffentlich angezeigt. Es gibt keine öffentliche Statistik und es werden keine Anmeldung oder E-Mail-Adresse verlangt.', 'The feedback is used only to improve this website internally. It is not displayed publicly. There is no public statistic, and no account or email address is required.'),
    entry('section:nth-of-type(7) p:nth-of-type(3)', 'Zum Schutz vor Spam und Mehrfachsendungen wird aus der vom Backend aufgelösten Client-Netzwerkadresse ein täglich wechselnder, geheimer HMAC-Hash für ein kurzlebiges Rate-Limit abgeleitet. Die vollständige IP-Adresse und dieser Hash werden nicht zusammen mit dem Feedback gespeichert. Zusätzlich werden ein unsichtbares Honeypot-Feld, Same-Origin- und Fetch-Metadata-Prüfungen sowie bekannte, von Cloudflare verifizierte Bots berücksichtigt. Das Rate-Limit erlaubt höchstens drei Einsendungen pro Stunde pro Rate-Limit-Schlüssel.', 'To prevent spam and repeated submissions, a daily changing secret HMAC hash is derived from the client network address resolved by the backend for a short-lived rate limit. The full IP address and this hash are not stored together with the feedback. An invisible honeypot field, same-origin and fetch-metadata checks, and known bots verified by Cloudflare are also used. The rate limit allows at most three submissions per hour per rate-limit key.'),
    entry('section:nth-of-type(7) p:nth-of-type(4)', 'Feedback-Einträge werden für höchstens 180 Tage vorgesehen. Ältere Einträge werden beim Start des Backends, beim Eingang einer neuen Rückmeldung oder beim Öffnen der internen Feedback-Ansicht gelöscht. Die interne Ansicht ist nur nach Anmeldung im bestehenden Admin-Bereich erreichbar und erscheint nicht in der normalen Navigation.', 'Feedback entries are retained for no more than 180 days. Older entries are deleted when the backend starts, when new feedback is received or when the internal feedback view is opened. The internal view is available only after signing in to the existing admin area and does not appear in the normal navigation.'),
    entry('section:nth-of-type(7) p:nth-of-type(5)', 'Kommentare werden serverseitig validiert und als Text gespeichert. Sie werden weder als HTML interpretiert noch auf der öffentlichen Website ausgegeben. Die interne Ansicht kodiert den Text zusätzlich vor der Darstellung.', 'Comments are validated server-side and stored as text. They are neither interpreted as HTML nor output on the public website. The internal view also escapes the text before rendering it.'),
    entry('section:nth-of-type(8) h2', 'Zweck und Rechtsgrundlage', 'Purpose and legal basis'),
    entry('section:nth-of-type(8) p:nth-of-type(1)', 'Die Verarbeitung dient dem berechtigten Interesse an der sicheren, stabilen und nachvollziehbaren Bereitstellung dieser persönlichen Website. Soweit die DSGVO anwendbar ist, stützt sich die Verarbeitung auf Art. 6 Abs. 1 lit. f DSGVO.', 'Processing serves the legitimate interest in providing this personal website securely, reliably and in a traceable way. Where the GDPR applies, processing is based on Art. 6(1)(f) GDPR.'),
    entry('footer', 'Stand: August 2026', 'Last updated: August 2026'),
  ];

  const entries = /datenschutz/.test(location.pathname) ? PRIVACY : IMPRESSUM;
  const style = document.createElement('style');
  style.textContent = '.legal-locale-switch{position:fixed;top:20px;right:24px;z-index:10;min-width:36px;padding:8px 10px;border:1px solid var(--line-2);border-radius:5px;background:rgba(27,31,46,.92);color:var(--ink-mute);font:11px var(--mono);cursor:pointer}.legal-locale-switch:hover{color:var(--acc);border-color:var(--acc)}.legal-locale-switch:focus-visible{outline:2px solid var(--acc);outline-offset:3px}@media(max-width:720px){.legal-locale-switch{top:14px;right:16px}}';
  document.head.appendChild(style);
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'legal-locale-switch';
  document.body.appendChild(button);

  function apply(locale){
    entries.forEach(item => {
      document.querySelectorAll(item.selector).forEach(el => {
        if(item.html) el.innerHTML = item[locale];
        else el.textContent = item[locale];
      });
    });
    document.querySelectorAll('a[href="index.html"], a[href="datenschutz.html"], a[href="impressum.html"], a[href^="/index.html"], a[href^="/datenschutz.html"], a[href^="/impressum.html"]').forEach(link => {
      const url = new URL(link.getAttribute('href') || '/', location.href);
      if(locale === 'en') url.searchParams.set('lang', 'en');
      else url.searchParams.delete('lang');
      link.setAttribute('href', url.pathname + (url.search ? url.search : '') + url.hash);
    });
    document.documentElement.lang = locale;
    document.title = /datenschutz/.test(location.pathname)
      ? (locale === 'en' ? 'Privacy policy | Ahmet Ilhan' : 'Datenschutz | Ahmet Ilhan')
      : (locale === 'en' ? 'Legal notice | Ahmet Ilhan' : 'Impressum | Ahmet Ilhan');
    const ui = localeApi.UI[locale];
    button.textContent = locale === 'en' ? 'DE' : 'EN';
    button.setAttribute('aria-label', ui.nav.switchTo);
    button.setAttribute('title', ui.nav.switchTo);
  }

  button.addEventListener('click', () => {
    const next = localeApi.get() === 'en' ? 'de' : 'en';
    localeApi.set(next);
    apply(next);
    const url = new URL(location.href);
    if(next === 'en') url.searchParams.set('lang', 'en');
    else url.searchParams.delete('lang');
    history.replaceState({}, '', url.pathname + (url.search ? url.search : '') + url.hash);
  });
  apply(localeApi.get());
})();
