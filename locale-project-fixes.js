/* Keep the project-page language control aligned with the portfolio shell. */
(function(){
  const style = document.createElement('style');
  style.textContent = `
    .project-locale-switch {
      position: fixed;
      top: 20px;
      right: 24px;
      z-index: 10;
      min-width: 42px;
      min-height: 36px;
      padding: 7px 10px;
      border: 1px solid var(--line-2);
      border-radius: 5px;
      background: rgba(22, 26, 40, .92);
      color: var(--ink-mute);
      font-family: var(--mono);
      font-size: 11px;
      cursor: pointer;
      transition: color .2s, border-color .2s, background .2s;
    }
    .project-locale-switch:hover,
    .project-locale-switch:focus-visible {
      color: var(--acc);
      border-color: rgba(109, 230, 162, .55);
      background: var(--bg-1);
      outline: none;
    }
    @media (max-width: 560px) {
      .project-locale-switch { top: 14px; right: 14px; }
    }
  `;
  document.head.appendChild(style);
  function syncBackLink(){
    const english = window.PortfolioLocale?.get() === 'en';
    document.querySelectorAll('.back').forEach(link => {
      link.setAttribute('href', english ? '/?lang=en' : '/');
    });
  }
  const observer = new MutationObserver(syncBackLink);
  observer.observe(document.body, {childList:true, subtree:true});
  syncBackLink();
})();
