export function validateFlashcardDeck(deck) {
  const text=x=>typeof x==='string'&&x.trim().length>0;
  if(deck?.version!==1||!text(deck.id)||!text(deck.title)||!text(deck.description)||!Array.isArray(deck.cards)||!deck.cards.length)throw Error('Invalid or empty flashcard deck.');
  const ids=new Set();
  for(const card of deck.cards){
    if(!['id','topic','section','prompt','concept','example','takeaway'].every(k=>text(card[k]))||ids.has(card.id))throw Error('Invalid or duplicate flashcard.');
    ids.add(card.id);
  }
  return deck;
}

export function setupFlashcards({isTimedQuizActive=()=>false}={}) {
  const $=id=>document.getElementById(id);
  const dialog=$('flashcard-dialog'),select=$('flashcards'),face=$('flashcard-face');
  let deck=null,order=[],position=0,flipped=false,request=0,path='';
  const cache=new Map();
  function render(){
    const card=deck.cards[order[position]];
    $('flashcard-progress').textContent=`Card ${position+1} of ${order.length}`;
    $('flashcard-topic').textContent=`${card.topic} · §${card.section}`;
    $('flashcard-side').textContent=flipped?'EXPLANATION & EXAMPLE':'RECALL THE CONCEPT';
    $('flashcard-prompt').textContent=card.prompt;
    $('flashcard-concept').textContent=card.concept;
    $('flashcard-example').textContent=card.example;
    $('flashcard-takeaway').textContent=card.takeaway;
    $('flashcard-front').hidden=flipped;
    $('flashcard-back').hidden=!flipped;
    face.setAttribute('aria-pressed',String(flipped));
    face.dataset.side=flipped?'back':'front';
    $('flashcard-flip').textContent=flipped?'Show prompt ↶':'Flip card ↷';
    $('flashcard-previous').disabled=position===0;
    $('flashcard-next').disabled=position===order.length-1;
    $('flashcard-shuffle').disabled=$('flashcard-flip').disabled=false;
    $('flashcard-announcement').textContent=`Card ${position+1} of ${order.length}. ${card.topic}. ${flipped?'Explanation and worked example shown.':'Recall prompt shown.'}`;
    $('flashcard-scroll').scrollTop=0;
  }
  function flip(){if(deck){flipped=!flipped;render();}}
  function move(delta){
    if(!deck)return;
    const next=position+delta;
    if(next<0||next>=order.length)return;
    position=next;flipped=false;render();
  }
  async function loadDeck(){
    const token=++request;
    deck=null;face.hidden=true;
    $('flashcard-status').hidden=false;
    $('flashcard-status').textContent='Loading flashcards…';
    $('flashcard-status').classList.remove('error');
    $('flashcard-retry').hidden=true;
    $('flashcard-progress').textContent='';$('flashcard-topic').textContent='';
    for(const id of ['flashcard-previous','flashcard-next','flashcard-shuffle','flashcard-flip'])$(id).disabled=true;
    try{
      let loaded=cache.get(path);
      if(!loaded){
        const response=await fetch(path);
        if(!response.ok)throw Error(`Unable to load flashcards (${response.status}).`);
        loaded=validateFlashcardDeck(await response.json());
      }
      if(token!==request||!dialog.open)return;
      cache.set(path,loaded);deck=loaded;
      order=deck.cards.map((_,i)=>i);position=0;flipped=false;
      $('flashcard-title').textContent=deck.title;
      $('flashcard-description').textContent=deck.description;
      $('flashcard-status').hidden=true;
      face.hidden=false;render();face.focus({preventScroll:true});
    }catch(error){
      if(token!==request||!dialog.open)return;
      $('flashcard-status').textContent=`${error.message} Retry to load this deck.`;
      $('flashcard-status').classList.add('error');
      $('flashcard-retry').hidden=false;
    }
  }
  select.addEventListener('change',()=>{
    if(!select.value)return;
    path=select.value;
    $('flashcard-title').textContent=select.selectedOptions[0].textContent;
    $('flashcard-description').textContent='Recall a concept, then flip for an explanation and worked example.';
    $('flashcard-timer-note').hidden=!isTimedQuizActive();
    dialog.showModal();loadDeck();
  });
  $('flashcard-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{request++;deck=null;select.value='';select.focus({preventScroll:true});});
  face.addEventListener('click',flip);
  $('flashcard-flip').addEventListener('click',flip);
  $('flashcard-previous').addEventListener('click',()=>move(-1));
  $('flashcard-next').addEventListener('click',()=>move(1));
  $('flashcard-retry').addEventListener('click',loadDeck);
  $('flashcard-shuffle').addEventListener('click',()=>{
    if(!deck)return;
    for(let i=order.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[order[i],order[j]]=[order[j],order[i]];}
    position=0;flipped=false;render();
  });
  dialog.addEventListener('keydown',event=>{
    if(event.altKey||event.ctrlKey||event.metaKey)return;
    if(event.key==='ArrowLeft'){event.preventDefault();move(-1);}
    if(event.key==='ArrowRight'){event.preventDefault();move(1);}
  });
}
