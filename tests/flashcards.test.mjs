import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateFlashcardDeck} from '../js/flashcards.js';
const deck=JSON.parse(await readFile(new URL('../data/flashcards/utd-midterm.json',import.meta.url),'utf8'));
test('flashcards cover all 19 midterm sections with complete concept/example pairs',()=>{
  assert.equal(validateFlashcardDeck(deck),deck);
  assert.equal(deck.cards.length,40);
  assert.deepEqual([...new Set(deck.cards.map(c=>c.section))].sort(),['1.1','1.3','1.4','1.5','1.6','1.7','1.8','2.1','2.2','2.3','2.4','2.5','2.6','3.1','3.2','3.3','4.1','4.2','4.3']);
  for(const card of deck.cards){
    assert.ok(card.example.length>70,card.id);
    assert.ok(!/\b(TODO|TBD|placeholder|medical)\b|�|Ã|â€/.test(JSON.stringify(card)),card.id);
  }
});
test('invalid, empty and duplicate flashcards cannot enter the viewer',()=>{
  for(const bad of [null,{}, {...deck,cards:[]},{...deck,cards:[deck.cards[0],deck.cards[0]]},{...deck,cards:[{...deck.cards[0],example:''}]}]){
    assert.throws(()=>validateFlashcardDeck(bad));
  }
});
