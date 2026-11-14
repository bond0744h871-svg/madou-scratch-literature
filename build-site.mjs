import { writeFileSync } from 'node:fs';
import { title, sources, reading, standards, prep, lessons, checkpoints, support } from './curriculum.mjs';

const repo = 'https://github.com/bond0744h871-svg/madou-scratch-literature';
const items = (values) => values.map(value => '<li>' + value + '</li>').join('');
const entries = (values) => values.map(([name, detail]) => '<dt>' + name + '</dt><dd>' + detail + '</dd>').join('');
const sessions = lessons.map(([name, goal, scratch, flow, steps], i) => {
  const number = i + 1;
  return '<details id="lesson-' + number + '"' + (number === 1 ? ' open' : '') + '><summary><span>第 ' + number + ' 節</span>' + name + '</summary><div class="inside"><dl>' +
    entries([['教學目標', goal], ['Scratch 設計目標', scratch]]) + '</dl><div class="columns"><div><h3>40 分鐘教學流程</h3><ol>' +
    items(flow.map(([mins, activity]) => '<strong>' + mins + ' 分鐘</strong> ' + activity)) + '</ol></div><div><h3>' +
    (number <= 8 ? 'Scratch 操作步驟' : 'Scratch 與影片操作') + '</h3><ol>' + items(steps) + '</ol></div></div></div></details>';
});
const modules = checkpoints.map(([name, check], i) => '<section class="module"><h3><small>第 ' + (2*i+1) + '–' + (2*i+2) + ' 節</small>' + name + '</h3><p class="check">' + check + '</p>' + sessions.slice(2*i, 2*i+2).join('') + '</section>').join('');

const html = `<!doctype html>
<html lang="zh-Hant-TW">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="國小六年級地景文學與 Scratch 課程，12 節課共 480 分鐘。"><title>${title}｜六年級課程</title><link rel="stylesheet" href="style.css"></head>
<body>
<header class="wrap top"><a href="./">水堀頭的時光信</a><nav aria-label="頁面導覽"><a href="#reading">閱讀</a><a href="#lessons">12 節課</a><a href="#references">來源</a></nav></header>
<main>
<section class="hero wrap">
<div class="hero-copy"><p class="meta">六年級｜12 節 × 40 分鐘</p><h1>水堀頭的<br>時光信</h1><p class="intro">從吳新榮的日記出發，為麻豆水堀頭寫一段故事。用 Scratch 做成可點選的三幕動畫，再剪出一支地景短片。</p><div class="actions"><a class="button" href="#lessons">查看教學流程</a><a class="button outline" href="materials/madou-scratch.pptx" download>下載教學簡報</a></div></div>
<figure><img src="assets/old-harbor.jpg" width="1672" height="941" alt="繪本插圖，背著黃書包的孩子望向一艘靠岸的木船"><figcaption>AI 生成繪本插圖｜想像中的麻豆舊港</figcaption></figure>
</section>
<section id="reading" class="wrap section"><h2>讀一段水堀頭</h2><div class="reading">${reading.map(([name, detail]) => '<article><h3>' + name + '</h3><p>' + detail + '</p></article>').join('')}</div><p class="inline-links"><a href="${sources[1][1]}">查閱吳新榮日記</a> · <a href="${sources[2][1]}">查閱文化部遺址資料</a> · <a href="assets/old-harbor.jpg" download>下載舊港插圖</a></p></section>
<section id="lessons" class="wrap section"><h2>12 節課怎麼上</h2><p class="intro">每兩節驗收一件階段作品。展開任一節可查看時間分配、教學目標與操作步驟。</p><div class="lesson-nav" aria-label="快速跳到課次">${lessons.map((_, i) => '<a href="#lesson-' + (i+1) + '">第 ' + (i+1) + ' 節</a>').join('')}</div>${modules}</section>
<section class="wrap section"><h2>學生可以照著做</h2><dl>${entries([
  ['線索卡｜第 2 節', '地名：水堀頭。史實：水堀頭曾是麻豆港所在。來源：文化部文化資產局。我的描寫：風穿過草叢，草葉沙沙響。'],
  ['三格分鏡｜第 4 節', '現在：「我來到水堀頭，聽見草葉沙沙響。」→ 想像舊港：「我想像一艘載糖的小船正要靠岸。」→ 回到現在：「你能指出剛才哪一幕是我的想像嗎？」'],
  ['背景與角色素材', '現在與回到現在可用教師自攝的地景照片，或用 Scratch 畫背景。下載繪本圖，匯入「想像舊港」那一幕。導覽員可選 Scratch 內建角色。'],
  ['測試紀錄｜第 6、8 節', '輸入：1｜預期：出現再想想的提示｜實際：＿＿｜需要修正：＿＿。另寫一筆輸入 2 的測試。'],
  ['剪輯表｜第 10 節', '範例：00:05–00:20｜地景介紹｜保留旁白和背景轉場｜字幕「這裡是麻豆水堀頭」。'],
])}</dl></section>
<section class="wrap section"><h2>課前準備與評量</h2><ol>${items(prep)}</ol><dl>${entries(support)}</dl><h3>108 課綱對應</h3><dl>${entries(standards)}</dl></section>
<section id="references" class="wrap section"><h2>閱讀與操作來源</h2><ol>${items(sources.map(([name, url]) => '<a href="' + url + '">' + name + '</a>'))}</ol></section>
</main><footer class="wrap"><a href="${repo}">在 GitHub 查看課程原始碼</a></footer>
<script>
function openLesson() {
  if (!/^#lesson-\\d+$/.test(location.hash)) return;
  const lesson = document.getElementById(location.hash.slice(1));
  if (lesson) { lesson.open = true; lesson.scrollIntoView(); }
}
window.addEventListener('hashchange', openLesson);
openLesson();
</script></body></html>`;

if (lessons.length !== 12 || checkpoints.length !== 6 || lessons.some(lesson => lesson[3].reduce((sum, [mins]) => sum + mins, 0) !== 40)) {
  throw new Error('課程須有 12 節、每節 40 分鐘和 6 次驗收');
}
writeFileSync(new URL('index.html', import.meta.url), html);
