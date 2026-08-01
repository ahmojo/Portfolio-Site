/* Localize project detail responses and keep the page language switchable. */
(function(){
  const localeApi = window.PortfolioLocale;
  if(!localeApi) return;

  const nativeFetch = window.fetch.bind(window);
  window.fetch = function(input, init){
    return nativeFetch(input, init).then(response => {
      const url = typeof input === 'string' ? input : input?.url || '';
      if(!url.includes('/api/project/') || !response.ok) return response;
      return response.clone().json().then(data => new Response(
        JSON.stringify(localeApi.localizeProject(data, localeApi.get())),
        {status: response.status, statusText: response.statusText, headers: response.headers},
      )).catch(() => response);
    });
  };

  const copy = () => localeApi.UI[localeApi.get()].project;
  const installSwitch = () => {
    if(document.getElementById('project-locale-switch')) return;
    const button = document.createElement('button');
    button.id = 'project-locale-switch';
    button.type = 'button';
    button.className = 'project-locale-switch';
    button.addEventListener('click', () => {
      const next = localeApi.get() === 'en' ? 'de' : 'en';
      localeApi.set(next);
      const url = new URL(location.href);
      if(next === 'en') url.searchParams.set('lang', 'en');
      else url.searchParams.delete('lang');
      location.href = url.pathname + (url.search ? url.search : '');
    });
    document.body.appendChild(button);
    const update = () => {
      const english = localeApi.get() === 'en';
      const ui = localeApi.UI[localeApi.get()];
      button.textContent = english ? 'DE' : 'EN';
      button.setAttribute('aria-label', ui.nav.switchTo);
      button.setAttribute('title', ui.nav.switchTo);
      document.documentElement.lang = localeApi.get();
    };
    update();
  };

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installSwitch, {once:true});
  else installSwitch();
})();
