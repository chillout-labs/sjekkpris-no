// Node-level interaction checks; not a browser/layout test.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const code = fs.readFileSync(path.join(__dirname, '../product_ui.py'), 'utf8')
  .split('PRICE_MODE_SCRIPT = r"""')[1].split('"""')[0];

function harness() {
  const nodes = ['item','total','item','total'].map(mode => ({dataset:{priceMode:mode},hidden:mode==='total'}));
  const root = {dataset:{},querySelectorAll:()=>nodes};
  const toggle = {checked:true,addEventListener:(name,fn)=>{toggle[name]=fn;}};
  const control = {hidden:true}, status = {textContent:''};
  const row = (name,itemOrder,totalOrder) => ({name, querySelector:()=>({dataset:{itemOrder,totalOrder}})});
  const rows = {children:[row('unknown',0,2),row('paid',1,1),row('free',2,0)],
    appendChild(el) { this.children.splice(this.children.indexOf(el),1); this.children.push(el); }};
  const elements = {'include-shipping':toggle,'shipping-switch-control':control,'price-rows':rows,'price-sort-status':status};
  vm.runInNewContext(code, {document:{querySelector:()=>root,getElementById:id=>elements[id]}});
  return {root,toggle,control,rows,nodes,status};
}

test('default is item price even if browser restores a checked input', () => {
  const h=harness();
  assert.equal(h.toggle.checked,false);
  assert.equal(h.control.hidden,false);
  assert.equal(h.root.dataset.priceBasis,'item');
  assert.deepEqual(h.nodes.map(n=>n.hidden),[false,true,false,true]);
});
test('toggle synchronizes hero, row amounts, order and accessible status; can toggle back', () => {
  const h=harness();
  h.toggle.checked=true; h.toggle.change();
  assert.equal(h.root.dataset.priceBasis,'total');
  assert.deepEqual(h.nodes.map(n=>n.hidden),[true,false,true,false]);
  assert.deepEqual(h.rows.children.map(r=>r.name),['free','paid','unknown']);
  assert.match(h.status.textContent,/ukjent totalpris vises sist/);
  h.toggle.checked=false; h.toggle.change();
  assert.deepEqual(h.nodes.map(n=>n.hidden),[false,true,false,true]);
  assert.deepEqual(h.rows.children.map(r=>r.name),['unknown','paid','free']);
});
test('empty page exits without an interactive toggle', () => {
  assert.doesNotThrow(()=>vm.runInNewContext(code, {document:{querySelector:()=>null,getElementById:()=>null}}));
});
