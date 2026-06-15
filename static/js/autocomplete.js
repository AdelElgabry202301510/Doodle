(function(){
  const input = document.getElementById('query-input');
  const root = document.getElementById('autocomplete-root');
  if(!input || !root) return;

  let controller = null;

  function clearRoot(){
    const existing = root.querySelector('.autocomplete-list');
    if(existing) existing.remove();
  }

  function renderList(items){
    clearRoot();
    if(!items || items.length===0) return;
    const ul = document.createElement('ul');
    ul.className='autocomplete-list';
    items.forEach(it=>{
      const li = document.createElement('li');
      li.textContent = it;
      li.addEventListener('mousedown', function(e){
        e.preventDefault();
        input.value = it;
        clearRoot();
      });
      ul.appendChild(li);
    });
    root.appendChild(ul);
  }

  async function fetchSuggestions(q){
    if(controller) controller.abort();
    controller = new AbortController();
    try{
      const res = await fetch('/autocomplete?q=' + encodeURIComponent(q), {signal: controller.signal});
      if(!res.ok) return [];
      const data = await res.json();
      return data;
    }catch(e){
      return [];
    }
  }

  let timer = null;
  input.addEventListener('input', function(e){
    const v = this.value.trim();
    if(timer) clearTimeout(timer);
    if(!v){ clearRoot(); return; }
    timer = setTimeout(async ()=>{
      const items = await fetchSuggestions(v);
      renderList(items);
    }, 180);
  });

  document.addEventListener('click', function(e){
    if(!root.contains(e.target) && e.target!==input){
      clearRoot();
    }
  });
})();
