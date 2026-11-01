/* works-detail 縦型スクショ ギャラリー（3Dカルーセル）
   使い方:
     <div class="wdv" id="wdv" data-variant="1" data-items='[{"src":"...","t":"..."}]'></div>
     <link rel="stylesheet" href="assets/works-gallery.css">
     <script src="assets/works-gallery.js"></script>
 */
(function(){
  'use strict';
  var root=document.getElementById('wdv');
  if(!root)return;
  var items;try{items=JSON.parse(root.getAttribute('data-items')||'[]')}catch(e){items=[]}
  var NV=items.length;if(!NV)return;

  var $=function(s,r){return (r||document).querySelector(s)};
  var $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var clamp=function(v,a,b){a=a==null?0:a;b=b==null?1:b;return Math.min(b,Math.max(a,v))};
  var lerp=function(a,b,t){return a+(b-a)*t};
  var ease=function(t){return 1-Math.pow(1-t,3)};
  var pad=function(n,l){n=String(n);while(n.length<(l||2))n='0'+n;return n};
  var esc=function(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* 画面内にあるときだけ動かすループ */
  var tasks=[];
  function reg(el,fn){var t={fn:fn,on:false};tasks.push(t);new IntersectionObserver(function(es){t.on=es[0].isIntersecting},{rootMargin:'250px'}).observe(el)}
  (function loop(ts){for(var i=0;i<tasks.length;i++)if(tasks[i].on)tasks[i].fn(ts);requestAnimationFrame(loop)})(0);

  function phone(inner,extra){return '<div class="wdv-phone '+(extra||'')+'"><div class="wdv-screen">'+inner+'</div></div>'}
  function img(i){return '<img src="'+esc(items[i].src)+'" alt="'+esc(items[i].t)+'" draggable="false" decoding="async">'}

  /* =========================== V4 3D Carousel ===========================
     遊び要素: マウスに追従する傾き / ドラッグの勢いで歪む / ダブルタップでハート /
              タップで手前に飛び出す / 横ホイールで回転 */
  function v4(){
    var slots=NV<6?items.concat(items):items,NS=slots.length;   /* 枚数が少ないときはリングが寂しいので繰り返す */
    var HEART='<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>';
    root.innerHTML='<section class="wdv-panel wdv-clip"><div class="wdv-v4-scene"><i class="wdv-v4-floor"></i><div class="wdv-v4-ring">'
      +slots.map(function(d){return '<div class="wdv-v4-item">'+phone('<img src="'+esc(d.src)+'" alt="'+esc(d.t)+'" draggable="false">')+'</div>'}).join('')
      +'</div><div class="wdv-v4-fx"></div></div><div class="wdv-ctl"><button class="prev" aria-label="前へ">←</button><button class="next" aria-label="次へ">→</button></div></section>';
    var scene=$('.wdv-v4-scene',root),ring=$('.wdv-v4-ring',root),fx=$('.wdv-v4-fx',root);
    var its=$$('.wdv-v4-item',ring),phs=its.map(function(it){return it.firstElementChild});
    var STEP=360/NS,R=300,PW=200,ang=0,avel=0,drag=false,lx=0,snap=null,lastAct=performance.now();
    var pop=0,popped=false,mx=0,my=0,tmx=0,tmy=0,down=null,lastTap={t:0,x:0,y:0},pending=null;

    function size(){PW=phs[0].offsetWidth;R=PW*.5/Math.tan(Math.PI/NS)+PW*.7;its.forEach(function(it,i){it.style.transform='rotateY('+(i*STEP)+'deg) translateZ('+R+'px)'})}
    size();addEventListener('resize',size);addEventListener('load',size);
    function frontSlot(){return((Math.round(-ang/STEP)%NS)+NS)%NS}
    function kick(){lastAct=performance.now()}
    function step(d){var base=snap==null?Math.round(ang/STEP)*STEP:snap;snap=base+d*STEP;avel=0;kick()}
    function gotoSlot(i){var want=-i*STEP,k=Math.round((ang-want)/360);snap=want+k*360;avel=0;kick()}
    function setPop(v){popped=v;scene.classList.toggle('popped',v);if(v)snap=Math.round(ang/STEP)*STEP;kick()}

    /* ハート（ダブルタップ） */
    var COL=['#ff3d7a','#ff7a1a','#8b5cf6','#2ec4b6','#ffd23f'];
    function heart(x,y){
      var h=document.createElementNS('http://www.w3.org/2000/svg','svg');h.setAttribute('viewBox','0 0 24 24');h.setAttribute('class','wdv-heart');h.innerHTML=HEART;
      var sc=.8+Math.random()*1.3;h.style.width=h.style.height=(26*sc)+'px';h.style.left=(x-13*sc)+'px';h.style.top=(y-13*sc)+'px';
      h.style.fill=COL[Math.floor(Math.random()*COL.length)];h.style.setProperty('--dx',(Math.random()*160-80)+'px');h.style.setProperty('--r',(Math.random()*70-35)+'deg');
      fx.appendChild(h);h.addEventListener('animationend',function(){h.remove()});
    }
    function burst(n,x,y){for(var i=0;i<n;i++)setTimeout(function(){heart(x+Math.random()*40-20,y+Math.random()*30-15)},i*65)}

    /* 操作 */
    scene.addEventListener('pointerdown',function(e){
      drag=true;down={x:e.clientX,y:e.clientY,moved:0};lx=e.clientX;if(!popped){avel=0;snap=null}kick();
      scene.classList.add('drag');scene.setPointerCapture(e.pointerId);
    });
    scene.addEventListener('pointermove',function(e){
      var r=scene.getBoundingClientRect();tmx=clamp((e.clientX-r.left)/r.width*2-1,-1,1);tmy=clamp((e.clientY-r.top)/r.height*2-1,-1,1);
      if(!drag)return;
      down.moved=Math.max(down.moved,Math.hypot(e.clientX-down.x,e.clientY-down.y));
      var d=e.clientX-lx;lx=e.clientX;
      if(!popped){ang+=d*.42;avel=d*.42}
      kick();
    });
    function up(e,cancel){
      if(!drag)return;drag=false;scene.classList.remove('drag');
      if(!cancel&&down&&down.moved<6)tap(e.clientX,e.clientY);
      down=null;
    }
    scene.addEventListener('pointerup',function(e){up(e,false)});
    scene.addEventListener('pointercancel',function(e){up(e,true)});
    scene.addEventListener('pointerleave',function(){tmx=0;tmy=0});
    function tap(x,y){
      var now=performance.now();
      if(now-lastTap.t<300&&Math.hypot(x-lastTap.x,y-lastTap.y)<34){
        clearTimeout(pending);lastTap.t=0;
        var r=scene.getBoundingClientRect();burst(10,x-r.left,y-r.top);return;
      }
      lastTap={t:now,x:x,y:y};
      pending=setTimeout(function(){single(x,y)},270);
    }
    function single(x,y){
      if(popped){setPop(false);return}
      var el=document.elementFromPoint(x,y),it=el&&el.closest?el.closest('.wdv-v4-item'):null,i=it?its.indexOf(it):-1;
      if(i<0)return;
      if(i===frontSlot())setPop(true);else gotoSlot(i);
    }
    document.addEventListener('pointerdown',function(e){if(popped&&!scene.contains(e.target))setPop(false)});
    addEventListener('keydown',function(e){if(e.key==='Escape'&&popped)setPop(false)});
    /* 横スクロール（トラックパッド / Shift+ホイール）でも回る。縦のページスクロールは邪魔しない */
    scene.addEventListener('wheel',function(e){
      var dx=Math.abs(e.deltaX)>Math.abs(e.deltaY)?e.deltaX:(e.shiftKey?e.deltaY:0);
      if(!dx||popped)return;e.preventDefault();ang-=dx*.28;avel=-dx*.12;snap=null;kick();
    },{passive:false});
    $('.prev',root).onclick=function(){if(popped)setPop(false);step(1)};
    $('.next',root).onclick=function(){if(popped)setPop(false);step(-1)};

    reg(scene,function(){
      var now=performance.now();
      /* 回転: 止まるときは弾まず、すっと位置に収まる */
      if(!drag){
        if(snap!=null){
          ang+=(snap-ang)*.14;
          if(Math.abs(snap-ang)<.05)ang=snap;
        }else{
          ang+=avel;avel*=.95;
          if(Math.abs(avel)<.12)snap=Math.round(ang/STEP)*STEP;
        }
        if(!reduce&&!popped&&snap!=null&&Math.abs(snap-ang)<.05&&now-lastAct>3600){snap-=STEP;lastAct=now-1200}
      }
      mx+=(tmx-mx)*.1;my+=(tmy-my)*.1;                            /* 傾き追従 */
      pop+=((popped?1:0)-pop)*.14;                                /* 飛び出し */
      var fit=Math.min(1.9,scene.clientHeight*1.08/(PW*1.844)),popExtra=Math.max(.15,fit-1.42);
      ring.style.transform='translateZ('+(-R)+'px) rotateY('+ang+'deg)';
      var vsk=clamp(avel*-.6,-13,13);
      for(var i=0;i<NS;i++){
        var f=(Math.cos((i*STEP+ang)*Math.PI/180)+1)/2,f4=f*f*f*f;
        var sc=1+.42*f4+f4*pop*popExtra;
        phs[i].style.transform='translate3d(0,'+(-f4*pop*8)+'px,0) scale('+sc.toFixed(4)+') rotateX('+(-my*15*f4*(1+pop)).toFixed(2)+'deg) rotateY('+(mx*20*f4*(1+pop)).toFixed(2)+'deg) skewX('+vsk.toFixed(2)+'deg)';
        its[i].style.opacity=((.3+.7*f)*(1-(1-f4)*pop*.9)).toFixed(3);
      }
    });
  }

  v4();

})();
