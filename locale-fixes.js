/* Small compatibility fixes for repeated/stat elements rendered by the page. */
(function(){
  function sync(locale){
    const english = locale === 'en';
    const aboutLabels = english
      ? ['3rd year · IMS', 'projects', 'certificates · Boot.dev', 'hackathon']
      : ['Jahr · IMS', 'Projekte', 'Zertifikate · Boot.dev', 'Hackathon'];
    document.querySelectorAll('#about .stat').forEach((stat, index) => {
      const label = stat.querySelector('.stat-l');
      if(label && aboutLabels[index]) label.textContent = aboutLabels[index];
    });

    const githubLabels = english
      ? ['commits · year', 'current streak', 'longest streak', 'public repos']
      : ['commits · Jahr', 'aktueller Streak', 'längster Streak', 'öffentliche Repos'];
    document.querySelectorAll('#gh-panel .gh-stat').forEach((stat, index) => {
      const label = stat.querySelector('.gh-stat-l');
      if(label && githubLabels[index]) label.textContent = githubLabels[index];
    });

    document.querySelectorAll('.proj-deep').forEach(link => {
      const arrow = link.querySelector('.arr');
      if(!arrow) return;
      const label = english ? 'read more' : 'mehr erfahren';
      link.firstChild.nodeValue = label + ' ';
      const url = new URL(link.href, location.href);
      if(english) url.searchParams.set('lang', 'en');
      else url.searchParams.delete('lang');
      link.href = url.pathname + (url.search ? url.search : '') + (url.hash ? url.hash : '');
    });
  }

  const original = window.__applyPortfolioLocale;
  if(original){
    window.__applyPortfolioLocale = function(next, updateUrl=true){
      const result = original(next, updateUrl);
      sync(window.__portfolioLocale || 'de');
      return result;
    };
  }
  sync(window.__portfolioLocale || 'de');
})();
