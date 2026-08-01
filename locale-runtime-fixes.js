/* Reapply small locale-dependent details after API content is rendered. */
(function(){
  function syncLinks(){
    const english = window.__portfolioLocale === 'en';
    document.querySelectorAll('.proj-deep').forEach(link => {
      const url = new URL(link.getAttribute('href') || '/', location.href);
      if(english) url.searchParams.set('lang', 'en');
      else url.searchParams.delete('lang');
      link.setAttribute('href', url.pathname + (url.search ? url.search : '') + url.hash);
    });
    document.querySelectorAll('a[href="impressum.html"], a[href="datenschutz.html"], a[href^="/impressum.html"], a[href^="/datenschutz.html"]').forEach(link => {
      const url = new URL(link.getAttribute('href') || '/', location.href);
      if(english) url.searchParams.set('lang', 'en');
      else url.searchParams.delete('lang');
      link.setAttribute('href', url.pathname + (url.search ? url.search : '') + url.hash);
    });
  }

  window.__syncPortfolioLocaleLinks = syncLinks;
  const observer = new MutationObserver(syncLinks);
  observer.observe(document.body, {childList:true, subtree:true});
  syncLinks();
})();
