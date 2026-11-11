
import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="Mini Battle Arena", page_icon="⚔️", layout="wide")

characters = {
    "전사": {
        "hp": 350, "damage": 40, "skill_damage": 100,
        "speed": 4.5, "color": "#df9147",
        "weapon": "대검", "skill": "회전 베기",
        "description": "강력한 대검으로 전방을 베어버린다."
    },
    "마법사": {
        "hp": 240, "damage": 30, "skill_damage": 120,
        "speed": 4, "color": "#a77aff",
        "weapon": "마법 지팡이", "skill": "메테오",
        "description": "마법 구체와 운석으로 적을 공격한다."
    },
    "궁수": {
        "hp": 280, "damage": 35, "skill_damage": 105,
        "speed": 5.5, "color": "#43c99b",
        "weapon": "엘븐 장궁", "skill": "연속 화살",
        "description": "빠른 연속 사격으로 적을 제압한다."
    }
}

st.markdown("""
<style>
.stApp {
    background: #101323;
    color: white;
}
h1,h2,h3 { color: #f4d28c !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style="text-align:center">⚔ MINI BATTLE ARENA</h1>
<p style="text-align:center;color:#aaa">
2D SIDE SCROLLING ACTION RPG
</p>
""", unsafe_allow_html=True)

character = st.selectbox("플레이 캐릭터", list(characters.keys()))
c = characters[character]

a, b, d = st.columns(3)
a.metric("❤️ 체력", c["hp"])
b.metric("⚔️ 무기", c["weapon"])
d.metric("✨ 스킬", c["skill"])

st.info(
    f"**{character}** | {c['description']} "
    "| A/D 이동 · W 점프 · J 공격 · K 스킬"
)

config = json.dumps(c, ensure_ascii=False)

html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {
    margin:0;
    background:#101323;
    color:white;
    font-family:Arial;
}
canvas {
    width:100%;
    background:#171b32;
    border:2px solid #55516e;
    border-radius:12px;
    display:block;
    touch-action:none;
}
.controls {
    display:flex;
    justify-content:center;
    flex-wrap:wrap;
    gap:9px;
    padding:12px;
}
button {
    padding:13px 20px;
    background:#34344f;
    color:white;
    border:1px solid #8a82a5;
    border-radius:10px;
    font-weight:bold;
    cursor:pointer;
    touch-action:none;
}
button:active { background:#9470d4; }
#status {
    text-align:center;
    color:#f6d58c;
    padding:8px;
    font-weight:bold;
}
</style>
</head>
<body>

<canvas id="game" width="1000" height="540"></canvas>

<div id="status">전투 준비 완료!</div>

<div class="controls">
<button id="left">◀ 이동</button>
<button id="right">이동 ▶</button>
<button id="jump">⬆ 점프</button>
<button id="attack">⚔ 공격 J</button>
<button id="skill">✨ 스킬 K</button>
<button id="reset">🔄 재시작</button>
</div>

<script>
const C = __CONFIG__;

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const status = document.getElementById("status");

const W=1000,H=540,GROUND=440;

let keys={};
let player,enemy,projectiles,effects,damageTexts;
let camera=0,frame=0,gameOver=false,result="";
let last=0,shake=0,combo=0,comboTime=0;

function reset(){
    player={
        x:150,y:GROUND-90,w:48,h:90,
        hp:C.hp,maxHp:C.hp,
        vy:0,grounded:true,facing:1,
        attack:0,skill:0,
        attackCD:0,skillCD:0,
        invincible:0
    };

    enemy={
        x:760,y:GROUND-82,w:60,h:82,
        hp:500,maxHp:500,
        attackCD:0
    };

    projectiles=[];
    effects=[];
    damageTexts=[];
    camera=0;
    combo=0;
    comboTime=0;
    gameOver=false;
    result="";
    status.innerText="⚔ 전투 시작!";
}

function rect(x,y,w,h,color){
    ctx.fillStyle=color;
    ctx.fillRect(x,y,w,h);
}

function circle(x,y,r,color){
    ctx.fillStyle=color;
    ctx.beginPath();
    ctx.arc(x,y,r,0,Math.PI*2);
    ctx.fill();
}

function bar(x,y,w,h,value,max,color){
    rect(x,y,w,h,"#252a43");
    rect(x,y,w*Math.max(0,value/max),h,color);
    ctx.strokeStyle="#ffffff";
    ctx.strokeRect(x,y,w,h);
}

function background(){
    let g=ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0,"#151e42");
    g.addColorStop(1,"#4b3850");
    rect(0,0,W,H,g);

    // 달
    circle(820,100,45,"#f6e7bb");

    // 성
    for(let i=0;i<6;i++){
        let x=(i*230-camera*.25)%1300;
        if(x< -150)x+=1300;

        rect(x,240,110,200,"#252c49");
        rect(x+25,180,60,80,"#303653");
        rect(x+48,145,15,45,"#303653");

        rect(x+20,275,15,30,"#e9b56a");
        rect(x+75,275,15,30,"#e9b56a");
    }

    // 바닥
    rect(0,GROUND,W,H-GROUND,"#303348");
    rect(0,GROUND,W,6,"#9b8c9b");

    for(let i=0;i<30;i++){
        let x=(i*70-camera)%W;
        if(x<0)x+=W;
        rect(x,470,35,4,"#57566c");
    }
}

function drawCharacter(p,isPlayer){
    const x=p.x-camera;
    const y=p.y;
    const color=isPlayer?C.color:"#8c4868";

    ctx.save();

    if(isPlayer && p.invincible>0 && frame%6<3)
        ctx.globalAlpha=.4;

    // 그림자
    ctx.fillStyle="#0a0a18";
    ctx.beginPath();
    ctx.ellipse(x+24,GROUND-3,31,8,0,0,Math.PI*2);
    ctx.fill();

    if(!isPlayer){
        // 몬스터 몸체
        rect(x+7,y+28,48,48,"#874a76");
        rect(x+12,y+7,38,35,"#c2a1a4");
        circle(x+18,y+20,4,"#ff4141");
        circle(x+43,y+20,4,"#ff4141");

        // 뿔
        ctx.fillStyle="#ded0d2";
        ctx.beginPath();
        ctx.moveTo(x+12,y+13);
        ctx.lineTo(x,y-7);
        ctx.lineTo(x+23,y+12);
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(x+45,y+13);
        ctx.lineTo(x+61,y-7);
        ctx.lineTo(x+35,y+12);
        ctx.fill();

        rect(x+12,y+76,13,10,"#403047");
        rect(x+38,y+76,13,10,"#403047");
        return;
    }

    // 망토
    ctx.fillStyle=isPlayer?"#49324e":"#333";
    ctx.beginPath();
    ctx.moveTo(x+12,y+28);
    ctx.lineTo(x-3,y+78);
    ctx.lineTo(x+43,y+70);
    ctx.lineTo(x+39,y+29);
    ctx.fill();

    // 다리 애니메이션
    let walk=Math.sin(frame*.25)*5;
    rect(x+12,y+69,12,20,"#333b58");
    rect(x+31,y+69,12,20,"#333b58");

    // 몸
    rect(x+8,y+28,33,43,color);
    rect(x+13,y+35,23,25,"#f2c69e");

    // 얼굴
    circle(x+24,y+16,17,"#edc29c");

    // 머리
    ctx.fillStyle="#282337";
    ctx.beginPath();
    ctx.moveTo(x+8,y+19);
    ctx.lineTo(x+9,y-2);
    ctx.lineTo(x+22,y+3);
    ctx.lineTo(x+41,y-1);
    ctx.lineTo(x+41,y+19);
    ctx.lineTo(x+30,y+10);
    ctx.fill();

    // 눈
    circle(
        x+(p.facing===1?32:15),
        y+17,2,"#252337"
    );

    // 어깨 방어구
    rect(x+5,y+31,12,13,"#d0b16c");
    rect(x+34,y+31,12,13,"#d0b16c");

    drawWeapon(p,x,y);

    ctx.restore();
}

function drawWeapon(p,x,y){
    ctx.save();

    let facing=p.facing;
    let swing=p.attack>0?Math.sin((12-p.attack)/12*Math.PI):0;

    if(C.weapon==="대검"){
        ctx.translate(x+25,y+48);
        ctx.scale(facing,1);

        ctx.rotate(-.8+swing*1.9);

        rect(8,-36,10,63,"#b9c7db");
        rect(3,-38,20,7,"#f1cf75");
        rect(10,20,6,17,"#72533e");

        ctx.fillStyle="#ffffff";
        ctx.beginPath();
        ctx.moveTo(8,-36);
        ctx.lineTo(13,-55);
        ctx.lineTo(18,-36);
        ctx.fill();
    }

    else if(C.weapon==="마법 지팡이"){
        rect(
            facing===1?x+40:x+2,
            y+17,5,65,"#94653e"
        );

        circle(
            facing===1?x+42:x+4,
            y+15,11,"#c7a1ff"
        );

        circle(
            facing===1?x+42:x+4,
            y+15,5,"#ffffff"
        );
    }

    else {
        ctx.translate(x+25,y+42);
        ctx.scale(facing,1);

        ctx.strokeStyle="#d9ae70";
        ctx.lineWidth=5;

        ctx.beginPath();
        ctx.arc(15,0,23,-1.4+swing,1.4+swing);
        ctx.stroke();

        rect(8,-4,30,4,"#9d7145");

        if(p.attack>0){
            ctx.strokeStyle="#e9d5a7";
            ctx.lineWidth=2;
            ctx.beginPath();
            ctx.moveTo(12,-23);
            ctx.lineTo(12,23);
            ctx.stroke();
        }
    }

    ctx.restore();
}

function hit(damage){
    if(enemy.hp<=0)return;

    enemy.hp=Math.max(0,enemy.hp-damage);

    combo++;
    comboTime=90;

    effects.push({
        x:enemy.x+30,
        y:enemy.y+35,
        life:25,
        color:"#ffe08a",
        size:15
    });

    damageTexts.push({
        x:enemy.x+30,
        y:enemy.y,
        value:Math.round(damage),
        life:40
    });

    shake=9;

    if(enemy.hp<=0){
        gameOver=true;
        result="승리";
        status.innerText="🏆 승리! 몬스터 처치!";
    }
}

function attack(){
    if(gameOver||player.attackCD>0)return;

    player.attack=12;
    player.attackCD=20;

    if(C.weapon==="대검"){
        if(Math.abs(enemy.x-player.x)<125){
            hit(C.damage);
        }

        effects.push({
            x:player.x+player.facing*70,
            y:player.y+38,
            life:18,color:"#ffd77b",size:65
        });
    }

    else if(C.weapon==="마법 지팡이"){
        projectiles.push({
            x:player.x+player.facing*55,
            y:player.y+35,
            vx:player.facing*11,
            damage:C.damage,
            color:"#b78aff",
            size:13
        });
    }

    else {
        projectiles.push({
            x:player.x+player.facing*55,
            y:player.y+36,
            vx:player.facing*15,
            damage:C.damage,
            color:"#72e8b1",
            size:6
        });
    }
}

function skill(){
    if(gameOver||player.skillCD>0)return;

    player.skill=35;
    player.skillCD=240;

    if(C.weapon==="대검"){
        effects.push({
            x:player.x+player.facing*75,
            y:player.y+40,
            life:40,color:"#ffad47",size:130
        });

        if(Math.abs(enemy.x-player.x)<230){
            hit(C.skill_damage);
        }
    }

    else if(C.weapon==="마법 지팡이"){
        effects.push({
            x:enemy.x+30,
            y:enemy.y+35,
            life:45,color:"#b77cff",size:100
        });

        projectiles.push({
            x:player.x+player.facing*45,
            y:player.y+25,
            vx:player.facing*8,
            damage:C.skill_damage,
            color:"#c58aff",
            size:24
        });
    }

    else {
        for(let i=0;i<5;i++){
            projectiles.push({
                x:player.x+player.facing*45,
                y:player.y+20+(i-2)*12,
                vx:player.facing*15,
                damage:C.skill_damage/5,
                color:"#70f0ae",
                size:6
            });
        }
    }

    status.innerText="✨ "+C.skill+" 발동!";
}

function update(dt){
    if(gameOver)return;

    frame++;

    if(keys.a||keys.arrowleft){
        player.x-=C.speed*dt;
        player.facing=-1;
    }

    if(keys.d||keys.arrowright){
        player.x+=C.speed*dt;
        player.facing=1;
    }

    if((keys.w||keys.arrowup)&&player.grounded){
        player.vy=-14;
        player.grounded=false;
    }

    player.vy+=.65*dt;
    player.y+=player.vy*dt;

    if(player.y+player.h>=GROUND){
        player.y=GROUND-player.h;
        player.vy=0;
        player.grounded=true;
    }

    player.x=Math.max(10,Math.min(2900,player.x));

    player.attackCD=Math.max(0,player.attackCD-dt);
    player.skillCD=Math.max(0,player.skillCD-dt);
    player.invincible=Math.max(0,player.invincible-dt);
    player.attack=Math.max(0,player.attack-dt);
    player.skill=Math.max(0,player.skill-dt);

    // 몬스터 AI
    let dx=player.x-enemy.x;

    if(Math.abs(dx)>65){
        enemy.x+=Math.sign(dx)*1.4*dt;
    }

    enemy.attackCD=Math.max(0,enemy.attackCD-dt);

    if(Math.abs(dx)<85&&enemy.attackCD<=0){
        enemy.attackCD=70;

        if(player.invincible<=0){
            player.hp=Math.max(0,player.hp-18);
            player.invincible=45;

            if(player.hp<=0){
                gameOver=true;
                result="패배";
                status.innerText="💀 패배!";
            }
        }
    }

    // 투사체 충돌
    projectiles.forEach(p=>{
        p.x+=p.vx*dt;

        if(
            Math.abs(p.x-(enemy.x+30))<35&&
            Math.abs(p.y-(enemy.y+40))<55&&
            !p.hit
        ){
            p.hit=true;
            hit(p.damage);
        }
    });

    projectiles=projectiles.filter(p=>!p.hit);

    effects.forEach(e=>e.life-=dt);
    effects=effects.filter(e=>e.life>0);

    damageTexts.forEach(d=>{
        d.y-=1.2*dt;
        d.life-=dt;
    });

    damageTexts=damageTexts.filter(d=>d.life>0);

    comboTime=Math.max(0,comboTime-dt);
    if(comboTime===0)combo=0;

    camera=Math.max(0,Math.min(player.x-300,2400));
}

function draw(){
    ctx.save();

    if(shake>0){
        ctx.translate(
            (Math.random()-.5)*shake,
            (Math.random()-.5)*shake
        );
        shake*=.8;
    }

    background();

    drawCharacter(enemy,false);
    drawCharacter(player,true);

    projectiles.forEach(p=>{
        circle(p.x-camera,p.y,p.size,p.color);

        ctx.shadowBlur=20;
        ctx.shadowColor=p.color;
        circle(p.x-camera,p.y,p.size*.7,"white");
        ctx.shadowBlur=0;
    });

    effects.forEach(e=>{
        ctx.globalAlpha=e.life/45;
        ctx.strokeStyle=e.color;
        ctx.lineWidth=5;
        ctx.beginPath();
        ctx.arc(
            e.x-camera,e.y,
            e.size*(1-e.life/45)+10,
            0,Math.PI*2
        );
        ctx.stroke();
        ctx.globalAlpha=1;
    });

    damageTexts.forEach(d=>{
        text(d.value+"!",d.x-camera,d.y,24,"#ffe47b");
    });

    ctx.restore();

    // HUD
    bar(20,20,280,20,player.hp,player.maxHp,"#4cdb8c");
    text("HERO HP "+Math.ceil(player.hp),20,62,18);

    bar(700,20,280,20,enemy.hp,enemy.maxHp,"#e84d66");
    text("MONSTER HP "+Math.ceil(enemy.hp),700,62,18);

    text("WEAPON: "+C.weapon,20,100,17);
    text(
        "SKILL: "+(player.skillCD<=0?"READY":
        Math.ceil(player.skillCD/60)+"s"),
        20,130,17,
        player.skillCD<=0?"#71f3b0":"#ffca73"
    );

    text("COMBO x"+combo,820,100,23,"#ffce67");

    if(gameOver){
        ctx.fillStyle="rgba(0,0,0,.75)";
        ctx.fillRect(0,0,W,H);
        text(result,W/2-70,H/2,48,
            result==="승리"?"#ffda73":"#ff6767");
    }
}

function loop(t){
    let dt=last?Math.min((t-last)/16.67,2):1;
    last=t;

    update(dt);
    draw();

    requestAnimationFrame(loop);
}

window.addEventListener("keydown",e=>{
    let k=e.key.toLowerCase();

    if(["arrowleft","arrowright","arrowup"," "].includes(k))
        e.preventDefault();

    keys[k]=true;

    if(k==="j"&&!e.repeat)attack();
    if(k==="k"&&!e.repeat)skill();
});

window.addEventListener("keyup",e=>{
    keys[e.key.toLowerCase()]=false;
});

function bind(id,key){
    let b=document.getElementById(id);

    b.addEventListener("pointerdown",e=>{
        e.preventDefault();
        keys[key]=true;
    });

    ["pointerup","pointercancel","pointerleave"].forEach(event=>{
        b.addEventListener(event,()=>keys[key]=false);
    });
}

bind("left","arrowleft");
bind("right","arrowright");
bind("jump","arrowup");

document.getElementById("attack").onclick=attack;
document.getElementById("skill").onclick=skill;
document.getElementById("reset").onclick=reset;

reset();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

html = html.replace("__CONFIG__", config)

components.html(html, height=700, scrolling=False)
