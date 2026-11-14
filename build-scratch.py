"""Build six editable Scratch 3 projects. Requires Pillow and the Scratch Cat SVG."""

import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "materials" / "scratch"
STAGE = (480, 360)

MESSAGES = {
    "幕1": "scene-now",
    "幕2": "scene-past",
    "幕3": "scene-return",
    "探索": "explore",
    "片尾": "credits",
}


def number(value):
    return [1, [4, str(value)]]


def message(value):
    return [1, [10, value]]


class ScriptBuilder:
    def __init__(self, target):
        self.blocks = target["blocks"]

    def block(self, opcode, *, inputs=None, fields=None, shadow=False):
        key = f"b{len(self.blocks) + 1}"
        self.blocks[key] = dict(
            opcode=opcode, next=None, parent=None, inputs=inputs or {},
            fields=fields or {}, shadow=shadow, topLevel=False,
        )
        for value in self.blocks[key]["inputs"].values():
            for child in value[1:]:
                if isinstance(child, str):
                    self.blocks[child]["parent"] = key
        return key

    def chain(self, *keys):
        for left, right in zip(keys, keys[1:]):
            self.blocks[left]["next"] = right
            self.blocks[right]["parent"] = left
        return keys[0]

    def script(self, *keys):
        self.blocks[self.chain(*keys)].update(
            topLevel=True, x=40 + 580 * sum(block["topLevel"] for block in self.blocks.values()), y=50,
        )

    def flag(self):
        return self.block("event_whenflagclicked")

    def receive(self, name):
        return self.block("event_whenbroadcastreceived", fields={"BROADCAST_OPTION": [name, MESSAGES[name]]})

    def send(self, name, wait=False):
        opcode = "event_broadcastandwait" if wait else "event_broadcast"
        return self.block(opcode, inputs={"BROADCAST_INPUT": [1, [11, name, MESSAGES[name]]]})

    def backdrop(self, name):
        menu = self.block("looks_backdrops", fields={"BACKDROP": [name, None]}, shadow=True)
        return self.block("looks_switchbackdropto", inputs={"BACKDROP": [1, menu]})

    def say(self, words, seconds):
        return self.block("looks_sayforsecs", inputs={"MESSAGE": message(words), "SECS": number(seconds)})


def costume(name, data, extension, center):
    digest = hashlib.md5(data).hexdigest()
    return dict(
        name=name, assetId=digest, md5ext=f"{digest}.{extension}", dataFormat=extension,
        bitmapResolution=1, rotationCenterX=center[0], rotationCenterY=center[1],
    ), data


def encode(image, extension):
    buffer = io.BytesIO()
    options = {"quality": 90} if extension == "jpeg" else {}
    image.save(buffer, format=extension.upper(), **options)
    return buffer.getvalue()


def scene(name, source):
    with Image.open(ROOT / "assets" / source) as source_image:
        image = ImageOps.fit(source_image.convert("RGB"), STAGE, centering=(0.5, 0.49))
    return costume(name, encode(image, "jpeg"), "jpg", (240, 180))


def text_art(font_path):
    def font(size):
        return ImageFont.truetype(str(font_path), size)

    button = Image.new("RGBA", (152, 38))
    draw = ImageDraw.Draw(button)
    draw.rounded_rectangle((0, 0, 151, 37), radius=9, fill="#285B56", outline="#fff8e9", width=2)
    draw.text((76, 19), "點我找線索", font=font(19), fill="white", anchor="mm")

    credits = Image.new("RGB", STAGE, "#f8f3e8")
    draw = ImageDraw.Draw(credits)
    draw.text((35, 29), "水堀頭的時光信", font=font(36), fill="#172e30")
    draw.line((36, 87, 444, 87), fill="#a67b4d", width=2)
    for y, line in [
        (107, "地景資料｜文化部文化資產局"),
        (138, "　　　　《麻豆水堀頭遺址》"),
        (178, "閱讀資料｜國家文化記憶庫"),
        (209, "　　　　《吳新榮日記》1956 年補記"),
        (251, "故事｜課程原創　插圖｜AI 生成"),
        (290, "按綠旗可以再看一次"),
    ]:
        draw.text((36, y), line, font=font(18), fill="#285b56")
    return (
        costume("點我找線索", encode(button, "png"), "png", (76, 19)),
        costume("片尾來源", encode(credits, "png"), "png", (240, 180)),
    )


def target(name, costumes, *, stage=False, layer=0, x=0, y=0, size=100, visible=True):
    result = dict(
        isStage=stage, name=name, variables={}, lists={}, broadcasts={}, blocks={}, comments={},
        currentCostume=0, costumes=[item[0] for item in costumes], sounds=[], volume=100, layerOrder=layer,
    )
    if stage:
        result.update(tempo=60, videoTransparency=50, videoState="off", textToSpeechLanguage=None)
    else:
        result.update(visible=visible, x=x, y=y, size=size, direction=90, draggable=False, rotationStyle="don't rotate")
    return result


def build(lesson, art):
    now, past, cat, button, credits = art
    returned = ({**now[0], "name": "回到現在"}, now[1])
    scenes = [now] if lesson == 2 else [now, past, returned]
    if lesson >= 8:
        scenes.append(credits)

    stage = target("Stage", scenes, stage=True)
    narrator = target("導覽員", [cat], layer=1, x=-172, y=-102, size=63)
    targets = [stage, narrator]
    s, n = ScriptBuilder(stage), ScriptBuilder(narrator)
    if lesson == 2:
        s.script(s.flag(), s.backdrop("現在"))
        n.script(
            n.flag(),
            n.say("這裡是麻豆水堀頭，從前是麻豆港所在。", 4),
            n.say("我停下腳步，聽見草葉沙沙響。", 4),
        )
        return targets, scenes + [cat]

    used = list(MESSAGES)[:3 if lesson == 4 else 4 if lesson == 6 else 5]
    stage["broadcasts"] = {MESSAGES[name]: name for name in used}
    sequence = [s.flag()]
    for name, backdrop in zip(used, scenes[:3]):
        sequence += [s.backdrop(backdrop[0]["name"]), s.send(name, wait=True)]
    if lesson >= 6:
        sequence.append(s.send("探索"))
    s.script(*sequence)

    lines = [
        "這裡是麻豆水堀頭。風穿過草叢，草葉沙沙響。",
        "我想像一艘載糖的小船靠岸，木船碰到岸邊，輕輕一響。",
        "我回過神來。剛才哪個畫面是我的想像？",
    ]
    if lesson == 12:
        lines[0] = "這裡是麻豆水堀頭，從前是麻豆港所在。你聽，草葉在風裡沙沙響。"
        lines[2] = "眼前只剩風和草聲。我像收到一封舊港寄來的信。"
    durations = (6, 7, 6) if lesson >= 10 else (4, 5, 4)
    for name, words, seconds in zip(used, lines, durations):
        actions = [n.receive(name)]
        if name == "幕1":
            actions.append(n.block("looks_show"))
        if name == "幕2":
            actions.append(n.block("motion_glidesecstoxy", inputs={"SECS": number(1), "X": number(-120), "Y": number(-102)}))
        if name == "幕3":
            actions.append(n.block("motion_gotoxy", inputs={"X": number(-172), "Y": number(-102)}))
        n.script(*actions, n.say(words, seconds))
    n.script(n.flag(), n.block("motion_gotoxy", inputs={"X": number(-172), "Y": number(-102)}))

    if lesson >= 6:
        clue = target("線索按鈕", [button], layer=2, x=151, y=-135, visible=False)
        targets.append(clue)
        c = ScriptBuilder(clue)
        c.script(c.flag(), c.block("looks_hide"))
        c.script(c.receive("探索"), c.block("looks_show"))
        answer = c.block("sensing_answer")
        equals = c.block("operator_equals", inputs={"OPERAND1": [3, answer, [10, ""]], "OPERAND2": message("2")})
        correct = c.say("答對了！港口有資料，這艘船是故事想像。", 5 if lesson >= 10 else 4)
        if lesson >= 8:
            c.chain(correct, c.send("片尾"))
            c.script(c.receive("片尾"), c.block("looks_hide"))
            n.script(n.receive("片尾"), n.block("looks_hide"))
            s.script(s.receive("片尾"), s.backdrop("片尾來源"))
        retry = c.say("再想想，旁白在哪裡說『我想像』？請再點一次。", 4)
        c.script(
            c.block("event_whenthisspriteclicked"),
            c.say("水堀頭曾是港口。想想剛才的小船是怎麼出現的。", 4),
            c.block("sensing_askandwait", inputs={"QUESTION": message("小船靠岸是哪一種？輸入 1 史料原句，或 2 故事想像。")}),
            c.block("control_if_else", inputs={"CONDITION": [2, equals], "SUBSTACK": [2, correct], "SUBSTACK2": [2, retry]}),
        )
        return targets, scenes + [cat, button]
    return targets, scenes + [cat]


def write_project(lesson, art):
    targets, assets = build(lesson, art)
    project = dict(targets=targets, monitors=[], extensions=[], meta={"semver": "3.0.0", "vm": "0.2.0", "agent": ""})
    destination = OUTPUT / f"madou-lesson-{lesson:02}.sb3"
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        archive.writestr("project.json", json.dumps(project, ensure_ascii=False, separators=(",", ":")))
        for name, data in {item[0]["md5ext"]: item[1] for item in assets}.items():
            archive.writestr(name, data)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cat", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    art = (
        scene("現在", "present-day.jpg"),
        scene("想像舊港", "old-harbor.jpg"),
        costume("Scratch 貓咪", args.cat.read_bytes(), "svg", (48, 50)),
        *text_art(args.font),
    )
    files = [write_project(lesson, art) for lesson in (2, 4, 6, 8, 10, 12)]
    with ZipFile(OUTPUT / "madou-all-scratch-projects.zip", "w", ZIP_DEFLATED) as archive:
        for project_file in files:
            archive.write(project_file, project_file.name)
