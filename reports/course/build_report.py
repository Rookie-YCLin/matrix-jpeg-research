"""Produce the editable course report from the canonical theory and verified figures."""
import argparse
import csv
import json
from pathlib import Path
import re

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from lxml import etree
from latex2mathml.converter import convert

ROOT = Path(__file__).resolve().parents[2]
PIN = "https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/86cf6e2e2a07c75ec179ad3448818ae3c4586fc8/"
UPSTREAM = "https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/"
TITLE = "SVD-QIM 量化步長對 JPEG 浮水印強韌性與影像品質之影響"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--figures", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--math-xsl", type=Path, required=True)
args = parser.parse_args()
transform = etree.XSLT(etree.parse(str(args.math_xsl)))
d = Document()
d.core_properties.title = TITLE
d.core_properties.author = "林易辰"
d.core_properties.subject = "國立中山大學 電機工程學系 矩陣理論及應用"


def element(tag, **values):
    item = OxmlElement(tag)
    for k, v in values.items():
        item.set(qn("w:" + k), str(v))
    return item


def format_section(sec):
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(3)
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    sec.footer_distance = Cm(1.5)


def numbered(sec, fmt, start):
    sec.footer.is_linked_to_previous = False
    sec._sectPr.append(element("w:pgNumType", fmt=fmt, start=start))
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(element("w:fldSimple", instr="PAGE"))


format_section(d.sections[0])
for st in d.styles:
    if st.type == WD_STYLE_TYPE.PARAGRAPH:
        st.font.name = "Times New Roman"
        st.font.size = Pt(12)
        st.font.color.rgb = RGBColor(0, 0, 0)
        fonts = st.element.get_or_add_rPr().rFonts
        for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            fonts.attrib.pop(qn("w:"+key), None)
        fonts.set(qn("w:eastAsia"), "DFKai-SB")
        fonts.set(qn("w:cs"), "Times New Roman")
normal = d.styles["Normal"].paragraph_format
normal.line_spacing = 1.5
normal.space_after = Pt(7)
normal.first_line_indent = Pt(24)
for name, size in (("Title", 23), ("Heading 1", 17), ("Heading 2", 14), ("Heading 3", 12)):
    st = d.styles[name]
    st.font.size = Pt(size)
    st.font.bold = True
    st.paragraph_format.first_line_indent = Pt(0)
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(7)
    st.paragraph_format.keep_with_next = True
    props = st.element.get_or_add_pPr()
    border = props.find(qn("w:pBdr"))
    if border is not None:
        props.remove(border)
for name in ("Figure", "Figure Caption", "Formula", "Table Text", "Cover Text"):
    st = d.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = d.styles["Normal"]
    st.paragraph_format.first_line_indent = Pt(0)
    st.paragraph_format.space_after = Pt(5)
d.styles["Figure"].paragraph_format.keep_with_next = True
d.styles["Formula"].paragraph_format.space_before = Pt(4)
d.styles["Table Text"].paragraph_format.line_spacing = 1.12
d.styles["Table Text"].paragraph_format.space_after = Pt(4)
d.styles["Figure Caption"].font.size = Pt(11)


def math(p, tex):
    # This source uses a TeX declaration followed by a single character.
    tex = re.sub(r"\\mathsf\s+T", r"\\mathsf{T}", tex)
    tex = re.sub(r"\\\|(.+?)\\\|", lambda m: r"{\Vert " + m.group(1) + r"\Vert}", tex)
    node = transform(etree.fromstring(convert(tex).encode())).getroot()
    p._p.append(node)


def reference(label, url):
    p = d.add_paragraph(style="Cover Text")
    link = element("w:hyperlink")
    link.set(qn("r:id"), p.part.relate_to(url, RT.HYPERLINK, is_external=True))
    run = element("w:r")
    props = element("w:rPr")
    props.append(element("w:color", val="254F73"))
    props.append(element("w:u", val="single"))
    run.append(props)
    node = element("w:t")
    node.text = label
    run.append(node)
    link.append(run)
    p._p.append(link)


def rich(p, value):
    value = re.sub(r"\[([^\]]+)\]\[[^\]]+\]", r"\1", value)
    for token in re.split(r"(\$[^$]+\$|\*\*[^*]+\*\*|§[^§]+§)", value):
        if not token:
            continue
        if token.startswith("$") and token.endswith("$"):
            math(p, token[1:-1])
        elif token.startswith("**") and token.endswith("**"):
            p.add_run(token[2:-2]).bold = True
        elif token.startswith("§") and token.endswith("§"):
            p.add_run(token[1:-1])
        else:
            p.add_run(token)
    return p


def paragraph(s, style=None):
    return rich(d.add_paragraph(style=style), s)


def center(s, style="Cover Text", before=0):
    p = paragraph(s, style)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    return p


def fig(name, caption, width=14.8):
    p = d.add_paragraph(style="Figure")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(args.figures / f"{name}.png"), width=Cm(width))
    paragraph(caption, "Figure Caption")


def table(data):
    t = d.add_table(rows=0, cols=len(data[0]))
    t.style = "Table Grid"
    for i, values in enumerate(data):
        row = t.add_row()
        row._tr.get_or_add_trPr().append(element("w:cantSplit"))
        if i == 0:
            row._tr.get_or_add_trPr().append(element("w:tblHeader"))
        for cell, value in zip(row.cells, values):
            p = cell.paragraphs[0]
            p.style = "Table Text"
            rich(p, value)
            p.paragraph_format.keep_with_next = i < len(data) - 1
            if i == 0:
                cell._tc.get_or_add_tcPr().append(element("w:shd", fill="E8EEF4"))
                for run in p.runs:
                    run.bold = True
    d.add_paragraph().paragraph_format.space_after = Pt(0)


def markdown(value):
    lines = value.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
        elif line == "$$":
            i += 1
            group = []
            while lines[i].strip() != "$$":
                group.append(lines[i])
                i += 1
            p = d.add_paragraph(style="Formula")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            math(p, " ".join(group))
            i += 1
        elif line.startswith("|"):
            group = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[: -]+", x) for x in row):
                    group.append(row)
                i += 1
            table(group)
        elif line.startswith("### "):
            d.add_heading(line[4:], level=2)
            i += 1
        else:
            paragraph(line)
            i += 1


source = (ROOT / "reports/SVD_QIM_MATRIX_THEORY.md").read_text(encoding="utf-8").replace(chr(96), "§")
canonical = (ROOT / "reports/G6_FINAL_PROJECT_REPORT.md").read_text(encoding="utf-8")


def extract(start, end):
    return source.split(start, 1)[1].split(end, 1)[0].strip()


def chapter(title):
    d.add_heading(title, 1)


center("國立中山大學　電機工程學系", before=52)
center("矩陣理論及應用　期末專題", before=12)
center("SVD-QIM 量化步長對 JPEG\n浮水印強韌性與影像品質之影響", "Title", 54)
center("林易辰　B143012007", before=46)
center("2026 年 11 月", before=12)

front = d.add_section(WD_SECTION_START.NEW_PAGE)
format_section(front)
numbered(front, "lowerRoman", 1)
chapter("摘要")
abstract = canonical.split("## 摘要", 1)[1].split("## 一、", 1)[0].strip()
markdown("\n".join(line for line in abstract.splitlines() if "關鍵字" not in line).replace("上游血小板圖片", "上游提供的血小板角色插畫"))
paragraph("關鍵詞　奇異值分解、量化索引調變、盲式數位浮水印、JPEG、位元錯誤率、PSNR")
d.add_heading("閱讀順序", 2)
for line in ("一　研究問題與配對設計", "二　從影像到區塊奇異值", "三　QIM 格點、排序與容錯", "四　從矩陣改量到影像 PSNR", "五　實測結果與研究限制", "六　結論與可重現性"):
    paragraph(line, "Cover Text")

body = d.add_section(WD_SECTION_START.NEW_PAGE)
format_section(body)
numbered(body, "decimal", 1)
chapter("一　研究問題與配對設計")
paragraph("圖 1 取自上游提供的血小板角色插畫 [2]。經過 JPEG 後，我們仍能辨認影像，卻無法單憑肉眼知道裡面的 32 位元訊息能否讀回。影像相似度量的是像素，位元錯誤率量的是解碼結果。兩者回答不同問題，應在同一攻擊條件下並列。")
fig("paired_crop", "圖 1　同位置裁切。左為原始 JPEG 解碼 RGB，中為原版 QF15，右為 G6 QF15。三圖使用相同裁切座標與顯示尺度。資料來源：合併的 PSNR 實驗與重生影像。")
markdown(extract("## 一、研究問題與比較基準", "## 二、"))
d.add_heading("研究貢獻與證據", 2)
paragraph("上游已在 d₁、d₂ 的初始化註解提出工程直覺：增大量化步長可能提高強韌性，也可能增加輸出失真 [2]。本專題將這項直覺縮小為一個可檢驗的問題，只改第一奇異值步長，固定其他條件，再並列 BER 與 PSNR。")
table([
    ["證據層次", "本文用途"],
    ["已知矩陣理論 [1]", "SVD、正交性、範數與奇異值擾動界。"],
    ["條件式推導 [1, 2]", "對應索引及理想格點成立時，求單票裕度；以固定正交基底推導區塊改量。"],
    ["受控實測 [3–6]", "同一圖、同一金鑰與 JPEG 設定下比較兩組參數。"],
    ["研究限制", "局部裕度無法單獨決定整段 BER；取捨未證明普遍成立。"],
])
paragraph("插畫來源可追溯至固定上游提交 [2]，但未取得足以確認插畫公開再製權的資料。含插畫版本供課堂審閱。公開版可移除圖 1、2、6 或取得授權後再使用；若使用另有明確授權的教學圖，應標為示意，並保持本實驗的數據來源。")
d.add_heading("把品質因子當作攻擊設定", 2)
paragraph("JPEG 以區塊轉換和量化降低精度，解碼像素因此可能改變。本研究把編解碼器當作黑盒，固定實作與色度取樣，再讀取實際輸出。QF 是傳給 Pillow 的品質設定，數字不表示保留多少百分比的訊息。")
fig("quality", "圖 2　原版同一含水印 PNG 在 QF5、15、50、95 各自編碼後的同位置裁切。QF95 為固定設定重生示例，檔案位元組與封存不同，差異原因未確認。此圖只用於辨識視覺差異，BER 仍以封存 CSV 為準。")
paragraph("主條件從原版掃描先選出。QF15 與 QF20 並列最高 BER，依預定規則取較小的 QF15。後續兩組均由各自的含水印 PNG 直接產生每個 JPEG 檔，避免把前一次壓縮累積到下一個測點。")

d.add_heading("配對設計如何隔離步長的影響", 2)
table([
    ["比較項目", "固定方式", "理由"],
    ["輸入和訊息", "同一張解碼 RGB、同一 32 位元序列、兩把金鑰皆為 1", "避免圖像內容及訊息排列同時改變"],
    ["嵌入與擷取", "兩端同步使用各組步長；第二步長皆為 20", "使同一個索引在兩端使用同一餘數尺度"],
    ["JPEG 攻擊", "各組由自己的 PNG 獨立編碼；同一 Pillow 設定", "避免二次編碼或色度取樣混入比較"],
    ["評分", "先完成盲擷取，之後逐位核對；PSNR 共用原圖參照", "隔離解碼與評分，讓兩組像素品質可比較"],
])
paragraph("同一來源並不表示兩個版本嵌入後的像素相同。G6 在寫入時已改變步長，因此各組必須由自己的含水印 PNG 產生攻擊檔。兩個版本的攻擊檔也不能互換使用，因為擷取端應沿用該版本的步長。")
chapter("二　從影像到區塊奇異值")
fig("flow", "圖 3　原版嵌入與擷取流程示意 [2]。上排由原圖產生含水印 PNG，下排從受測影像讀回位元。JPEG 攻擊位於兩排之間。來源：固定版上游核心程式與 bit 介面。")
paragraph("在原版流程中，影像先轉入三個色彩通道，每個通道做 Haar DWT，取近似子頻帶的完整區塊。DCT 提供區塊內的頻率表示，係數重排由金鑰決定。SVD 最後將重新整形後的矩陣分解，讓嵌入端能在固定方向上只改兩個大小。擷取端重做同一流程，才有可能讀到相同位置所承載的訊息。")
markdown(extract("### 2.1 SVD 與嵌入矩陣", "### 2.2"))
d.add_heading("先用小矩陣看方向與大小", 2)
paragraph("以對角元素為 5 與 2 的二階矩陣為例。兩個秩一方向分別只在左上和右下有非零值，奇異值就是這兩個方向的大小。若改成 6 與 2，重建只在第一方向增加 1。一般影像區塊的奇異向量不與座標軸對齊，同樣大小的改量會分散到區塊元素。")

d.add_heading("三種分解各處理哪個問題", 2)
paragraph("Haar DWT 的近似係數可以先想成相鄰像素的加權總和，細節係數則保留方向上的差。原版選擇近似子頻帶的完整區塊，把其他細節留給逆轉換。DCT 接手的是每個 4×4 區塊，將區塊元素改寫成各種振盪樣式的係數。此步保持整個區塊的平方和，卻重新組織了座標。")
paragraph("排列 16 個 DCT 係數仍保持平方和，但把同一組數重排成不同的矩陣，奇異值通常會變。因此嵌入與擷取必須用同一排列。SVD 解決的是排列完成後如何把矩陣表示成一組彼此正交的秩一方向，以及各方向所乘的大小。這也是原版可以只更新兩個對角元素，然後用原來方向重建的原因。")
chapter("三　QIM 格點、排序與容錯")
markdown(extract("### 2.2 量化格點與局部裕度", "## 三、"))
fig("qim", "圖 4　QIM 餘數格點示意。區間端點週期相接，最近判決邊界距理想格點為 d/4。上下兩排採相同橫軸尺度。")
d.add_heading("從兩張區塊票到一個訊息位元", 2)
table([
    ["第一票", "第二票", "融合分數"],
    ["0", "0", "0"],
    ["0", "1", "1/4"],
    ["1", "0", "3/4"],
    ["1", "1", "1"],
])
paragraph("例如第一票讀成 0、第二票讀成 1，區塊分數仍只有 1/4。跨區塊及通道平均之後，這個分數只是整個訊息位置的一個貢獻。原版一維 K-means 再以兩群平均值反覆調整分界，最後才還原訊息位元次序。因此局部裕度、分群分界和最終 BER 分屬三個層次。")
d.add_heading("同一區塊的擾動界", 2)
markdown(extract("## 三、JPEG 有效擾動與理想局部充分條件", "## 四、"))

d.add_heading("把單票條件帶入一個區塊", 2)
paragraph("考慮一個教學用區塊，第一項原始奇異值為 113，訊息位元為 0。原版 d₁＝36 的區間索引是 3，嵌入值為 117；G6 d₁＝90 的區間索引是 1，嵌入值為 112.5。假設兩個版本在存成 PNG 後都維持第一項的理想位置，並假設攻擊對第一奇異值的有號改量為 +12。這組假設只用來觀察門檻。")
table([
    ["理想教學算例", "原版 d₁＝36", "G6 d₁＝90"],
    ["嵌入值及餘數", "117；餘數 9", "112.5；餘數 22.5"],
    ["加上 12 後的餘數", "129 除以 36 餘 21", "124.5 除以 90 餘 34.5"],
    ["擷取門檻與結果", "21 > 18，判為 1", "34.5 ≤ 45，判為 0"],
])
paragraph("同樣的奇異值改量在這個例子中跨過原版門檻，卻留在 G6 的原判決區間。這個 +12 是指定的奇異值改量，沒有把 JPEG QF 換算成 12。若已知的是矩陣擾動的譜範數小於 22.5，前一節的不等式能替 G6 的局部票提供保證。原版若超過 9，則只是原來的充分條件不再適用；還需看擾動方向與實際餘數才能判斷。")
paragraph("即使兩個版本都使用同一 JPEG 設定，嵌入影像已因步長不同而改變，各版本的有效擾動也可能不同。因此上表不代表把同一個擾動套進兩條實際影像管線。真正的比較來自固定設定下各自重新解碼的影像及位元。")
chapter("四　從矩陣改量到影像 PSNR")
markdown(extract("## 四、從區塊修改量到整圖 PSNR", "### 4.3"))
d.add_heading("用兩組像素比較分辨失真來源", 2)
paragraph("第一個比較固定原始解碼像素，量測兩個版本各自的含水印 PNG。第二個比較仍固定同一原始解碼像素，改用兩個版本各自的 QF15 解碼影像。這樣能分開觀察嵌入後與攻擊後的像素品質，也避免把不同原圖或不同比較階段混在一起。")

d.add_heading("將 PSNR 差換回 MSE 比值", 2)
paragraph("若想知道 −1.671 dB 在平方誤差尺度上表示什麼，可以對 PSNR 差取反後除以 10，再作 10 的次方。這個換算的前提是同一參照和峰值，且兩組 MSE 都大於零。對本次 QF15 CSV，114.211263 除以 77.730415 約為 1.469，所以 G6 的最終 RGB 均方誤差約為原版的 1.47 倍。此比值描述像素差，不能直接換算成人眼感受到的畫質差。")
chapter("五　實測結果與研究限制")
fig("ber", "圖 5　正式 32 位元訊息的 BER–QF 曲線。各標記為實際測點，折線只輔助閱讀。來源：正式逐位 BER CSV [4]。")
markdown(extract("## 五、已驗證 BER 與研究限制", "## 六、"))
fig("paired", "圖 6　原始解碼 RGB、原版 QF15 與 G6 QF15 全圖。來源：固定配對實驗重生影像，QF15 兩組 JPEG 雜湊與封存一致。")
d.add_heading("QF15 的配對畫質與可靠度", 2)
fig("psnr", "圖 7　嵌入 PNG 與 QF15 JPEG 的配對 PSNR。各棒使用同一原始解碼 RGB 參照。來源：配對 PSNR CSV [6]。")
psnr_section = extract("### 4.3 QF15 配對畫質實測", "## 五、")
for line in psnr_section.splitlines():
    if line.lstrip().startswith("|"):
        break
    if line.strip() and not line.lstrip().startswith("#"):
        lead = paragraph(line)
        lead.paragraph_format.keep_with_next = True
markdown(psnr_section[psnr_section.index("|"):])
d.add_heading("從證據能回答到哪裡", 2)
table([
    ["問題", "可以支持的說法"],
    ["理想格點離邊界多遠？", "在排序與索引相容前提下，第一票理想裕度由 9 增至 22.5。"],
    ["整個解碼器一定能成功嗎？", "不能由區塊界推出。三通道、跨區塊平均和分群仍影響輸出。"],
    ["品質代價是多少？", "本圖主條件的最終 JPEG PSNR 差為 −1.671 dB；未測主觀可見度。"],
    ["QF15 全反相有何解釋？", "封存位元證明原版輸出逐位互補，機制尚未證實。"],
    ["結果能普遍成立嗎？", "單圖、有限步長候選與離散 QF 實測，QF5 還出現退步。"],
])

d.add_heading("讀圖時不能跨過的界線", 2)
paragraph("曲線上的 19 個標記才是實際測點。相鄰測點用折線相連，不代表中間品質設定經過測試，也不代表 BER 隨 QF 單調變化。在 QF25 至 95 的既定測點，兩組皆為零錯誤。這部分能說明 G6 維持了已觀察的結果，無法拿來增加 QF15 的改善幅度。")
paragraph("兩組額外訊息的用途是確認候選選定後，換一組 32 位元內容是否仍能重現 QF15 的觀察。它們與主訊息共用同一圖、相同金鑰和編碼條件，且其中一組是主訊息的逐位互補。因此三組訊息不能當成三張獨立影像，也不應用來估計跨影像的統計置信度。")
d.add_heading("候選選擇與 QF15 分群診斷", 2)
with (ROOT / "outputs/svd-qim-qf15-exploration/results.csv").open(encoding="utf-8", newline="") as f:
    errors = {(int(r["d1"]), int(r["qf"])): r["errors"] for r in csv.DictReader(f) if r["d2"] == "20"}
table([["(d₁, d₂)", "QF10", "QF15", "QF20", "QF25"]] +
      [[f"({step}, 20)", *(errors[step, q] for q in (10, 15, 20, 25))] for step in (36, 60, 72, 90)])
paragraph("表列原始探索 CSV 的錯誤數，各格分母為 32 [5]。60 與 72 在 QF15 均為零錯誤，但在 QF10 分別錯 32 與 29 位元。90 在表列四點皆為零，是有限候選中的工程選擇。此表沒有涵蓋所有參數，也未求得理論最優解。")
paragraph("原版在 QF15 與 QF20 的輸出均逐位互補 [4]。區塊內先以 3:1 融合兩個奇異值的票，之後對同一訊息位置跨區塊與三通道平均。原版最後以一維 K-means 將高分群標為 1，再還原訊息位置 [2]。")
diagnosis = json.loads((Path(__file__).parent / "qf15-diagnostic.json").read_text(encoding="utf-8"))
diagnostic_rows = [["版本", "真值 0 分數", "真值 1 分數", "群中心", "閾值"]]
for key, label in (("upstream", "原版"), ("svd_step_90", "G6")):
    row = diagnosis["variants"][key]
    interval = lambda tag: "–".join(f"{v:.4f}" for v in row["truth_group_ranges"][tag])
    diagnostic_rows.append([label, interval("0"), interval("1"),
                            " / ".join(f"{c:.4f}" for c in row["centers"]), f'{row["threshold"]:.4f}'])
table(diagnostic_rows)
paragraph("兩組 QF15 JPEG 均符合封存雜湊。診斷擷取未使用真值，完成後才按真值分組。原版真值 0 的分數全高於真值 1，顯示分群前的分數已呈反向；G6 分數呈同向。這可解釋 QF15 的最終標籤，但上游哪個前置步驟造成分數反向仍未證實，QF20 未做同一診斷。完整 32 分數、中心、閾值與逐位輸出另存 [7]。")

d.add_heading("用位元與像素兩條證據回答主問題", 2)
paragraph("在 QF15，原版的分母與候選的分母都是 32。原版每個位置都錯，G6 每個位置都對，所以差值為 −100 個百分點。相對降幅則以原版 BER 為分母，這次也剛好是 100%。兩個數字的單位和意義不同。若原版 BER 已為零，相對降幅無法定義，此時應直接說兩組觀察到的錯誤數相同。")
paragraph("PSNR 的分母來自整張影像的三個通道。就算兩個版本的圖都能辨認，G6 仍可能有較大的平方差。圖 6 的全圖用來確認比較的是同一內容，圖 1 的裁切用來察看同一區域。兩圖沒有量化主觀可見度。數字比較仍以全圖 CSV 為準，不能拿局部裁切估計全圖 PSNR。")
paragraph("這次比較可用兩個問題收束：若目標是在指定 QF15 讀回訊息，這個固定案例支持採用 G6；若目標同時要求維持原版的像素品質，則必須納入實測的 1.671 dB 差距。兩項證據應並列，沒有一個只靠 BER 就能回答的單一畫質判準。")
d.add_heading("從有限測點判讀這次取捨", 2)
paragraph("以 QF15 為主的理由來自原版掃描，並不依賴 G6 曲線。先凍結主條件，才能判斷後續的改善是否回答同一問題。若讀者以另一個品質因子為實際使用條件，應直接看該點原版與 G6 的配對值，不能用主條件的結果代替。例如 QF20 也觀察到改善，但 QF5 的錯誤數上升，顯示結果隨攻擊設定而異。")
paragraph("從畫質角度看，QF15 的 −1.671 dB 是兩個版本之間的差距。若有部署上的畫質要求，應先定義可接受門檻，再用同一參照影像檢查兩組值。本文沒有設定主觀畫質門檻，所以只能指出像素品質下降的大小，不能宣稱人眼一定察覺或一定無法察覺。")
paragraph("量化步長的取捨也不能從一張圖決定通用設定。本研究提出的是固定實驗條件下的受控改動，以及可以被獨立重算的比較方式。若改用另一張圖片或另一個 JPEG 編碼器，應先固定輸入與比較指標，再依同樣方法逐點量測，不能沿用本圖的 BER 或 PSNR 作為預測值。")
chapter("六　結論與可重現性")
markdown(extract("## 六、結論", "## 來源與重現"))
d.add_heading("重跑順序與稽核", 2)
paragraph("以封存 commit 86cf6e2 為依據，使用 Python 3.13、固定 blind_watermark 上游 SHA 與各 manifest 所列版本。從倉庫根目錄執行下列程式，所有輸出目錄須事前不存在。將新結果與封存 CSV 逐列比對，並比對來源影像和 JPEG 雜湊。")
code = d.styles.add_style("Command", WD_STYLE_TYPE.PARAGRAPH)
code.base_style = d.styles["Cover Text"]
code.font.name = "Consolas"
code.font.size = Pt(10)
for line in (
    "python -m experiments.svd_qim_validation --output-dir <ber>",
    "python -m experiments.svd_qim_psnr --output-dir <paired>",
    "python -m reports.course.diagnose_qf15 --paired <paired> --output <json>",
    "python reports/course/build_figures.py --paired <paired> --output <figures>",
):
    paragraph(line, "Command")
paragraph("圖表來源依證據分流。BER 與 PSNR 直接讀取已合併 CSV；影像面板取自可重生檔案並以 manifest 查核；格點與流程圖屬數學與程式示意。畫面裁切採同位置，未做對比度拉伸。影像品質設定與 PNG／JPEG 封存差異詳見圖源紀錄。")
d.add_heading("從 CSV 重算論文中的數字", 2)
paragraph("BER 檔的 expected_bits 與 extracted_bits 必須各有 32 個位置。逐位比較得到錯誤位置清單，錯誤數等於清單長度。先對主訊息、原版與 G6、QF15 取出兩筆資料，再核對封存雜湊。這一層查核能區分擷取輸出是否相同，以及實際讀入的檔案是否相同。")
paragraph("PSNR 檔先按階段與版本分組。以 CSV 的全精度 MSE 代回同一公式，分別重算四個 PSNR。先作同階段版本差，再將差值四捨五入至三位。兩個階段不能互相抵扣。歷史 BER CSV 與此次 PSNR 重生檔的 PNG 雜湊有差異，故嵌入後 PSNR 明確引用本次產物；QF15 JPEG 則有檔案雜湊及擷取位元兩項一致證據。")
d.add_heading("參考資料", 1).paragraph_format.page_break_before = True
reference("[1] Bernstein（2009），Matrix Mathematics，第 2 版", "https://press.princeton.edu/books/paperback/9780691140391/matrix-mathematics")
paragraph("印刷頁 301–303（定義 5.6.1、定理 5.6.4）、547（式 9.2.5–9.2.7）、549（式 9.2.15）、562（命題 9.6.8、式 9.6.19）。", "Cover Text")
reference("[2] 固定上游核心 bwm_core.py", UPSTREAM + "blind_watermark/bwm_core.py")
reference("　公開 bit 介面與金鑰還原", UPSTREAM + "blind_watermark/blind_watermark.py")
reference("　上游提供的血小板角色插畫", UPSTREAM + "examples/pic/ori_img.jpeg")
reference("[3] d₁ 最小修改 patch", PIN + "patches/bwm_core_svd_d1_90.patch")
for label, slug in (("[4] 正式 BER", "svd-qim-qf15-selected"), ("[5] 15 組候選", "svd-qim-qf15-exploration"), ("[6] 配對 PSNR", "svd-qim-psnr-qf15")):
    reference(label + " CSV", PIN + f"outputs/{slug}/results.csv")
    reference("　環境、JPEG 設定及雜湊 manifest", PIN + f"outputs/{slug}/manifest.json")
v2 = "https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/codex/g6-course-report-v2/"
reference("[7] QF15 分群診斷完整資料", v2 + "reports/course/qf15-diagnostic.json")
reference("　診斷程式", v2 + "reports/course/diagnose_qf15.py")
reference("[8] BER 重現程式", PIN + "experiments/svd_qim_validation.py")
reference("　PSNR 重現程式", PIN + "experiments/svd_qim_psnr.py")
reference("　Research CI", "https://github.com/Rookie-YCLin/matrix-jpeg-research/actions")
paragraph("[9] 周孜燦，資料結構 Quick Review of C++，課堂講義。用於安排例子與定義的教學順序。", "Cover Text")
paragraph("[10] 國立中山大學研究生學位論文格式規範，第十四至十六點。參考紙張、字體、頁碼與圖源格式。", "Cover Text")
args.output.parent.mkdir(parents=True, exist_ok=True)
d.save(args.output)
