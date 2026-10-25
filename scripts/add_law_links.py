# -*- coding: utf-8 -*-
"""
为 content/topics 下每个专题 Markdown 追加"相关权威链接"区块。
- 每个专题都包含"中华人民共和国最高人民法院（官网）"链接（用户要求 1）。
- 每个专题按学科映射，链接其对应法律的官方全文（用户要求 2）。
- 幂等：若文件已含"## 相关权威链接"则跳过。
"""
import os

TOPICS_DIR = os.path.join(os.path.dirname(__file__), "..", "content", "topics")

SUPREME_COURT = "https://www.court.gov.cn/"

# 法律全称 -> 官方全文链接
LAW_URLS = {
    "宪法": "https://www.gov.cn/guoqing/2018-03/22/content_5276318.htm",
    "民法典": "https://www.court.gov.cn/zixun/xiangqing/233181.html",
    "刑法": "http://gongbao.court.gov.cn/Details/f8e30d0689b23f57bfc782d21035c3.html",
    "民事诉讼法": "http://gongbao.court.gov.cn/Details/886331ece0f6611a370642e89f08c6.html",
    "刑事诉讼法": "https://www.spp.gov.cn/zdgz/201810/t20181027_396818.shtml",
    "行政诉讼法": "https://www.gov.cn/xinwen/2017-07/05/content_5243206.htm",
    "行政处罚法": "http://www.npc.gov.cn/c2/c30834/202101/t20210122_309857.html",
    "行政许可法": "http://www.npc.gov.cn/npc/c2/c30834/201906/t20190608_298033.html",
    "行政强制法": "http://www.npc.gov.cn/c4146/c10825/201905/t20190522_51060.html",
    "行政复议法": "http://www.npc.gov.cn/c2/c30834/202309/t20230901_431409.html",
    "国家赔偿法": "https://www.court.gov.cn/zixun/xiangqing/7199.html",
    "公司法": "http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html",
    "证券法": "http://www.npc.gov.cn/c2/c30834/201912/t20191231_304436.html",
    "企业破产法": "http://www.npc.gov.cn/npc//c2/c183/c198/201905/t20190522_25968.html",
    "反垄断法": "http://www.npc.gov.cn/npc///c2/c183/c198/201905/t20190522_27381.html",
    "合伙企业法": "http://www.npc.gov.cn/npc/c2/c183/c198/201905/t20190522_25878.html",
    "劳动合同法": "http://www.npc.gov.cn/c2/c183/c198/201905/t20190522_26978.html",
    "环境保护法": "http://www.npc.gov.cn/npc/c1773/c2518/2019zhhbsjx/sjxflfg/201906/t20190628_260207.html",
    "涉外民事关系法律适用法": "http://www.npc.gov.cn/cwhhdbdh/c4186/c14354/c14359/201905/t20190523_400431.html",
    "联合国国际货物销售合同公约": "https://www.un.org/zh/documents/treaty/UNCITRAL-1980",
    "维也纳外交关系公约": "https://www.mfa.gov.cn/web/wjb_673085/zfxxgk_674865/gknrlb/tywj/tyqk/200404/t20040408_7949263.shtml",
}


def source_of(url):
    if "gongbao.court.gov.cn" in url:
        return "最高人民法院公报"
    if "court.gov.cn" in url:
        return "最高人民法院"
    if "npc.gov.cn" in url:
        return "中国人大网"
    if "mfa.gov.cn" in url:
        return "外交部"
    if "gov.cn" in url:
        return "中国政府网"
    if "spp.gov.cn" in url:
        return "最高人民检察院"
    if "un.org" in url:
        return "联合国"
    if "mfa.gov.cn" in url:
        return "外交部"
    return "官方"


# slug(文件名去 .md) -> 该专题涉及的法律列表（顺序即展示顺序）
MAPPING = {
    # 民法
    "minfa": ["民法典"],
    "minfa-zongze": ["民法典"],
    "minfa-danbao": ["民法典"],
    "minfa-rengge": ["民法典"],
    "minfa-wuquan-bian": ["民法典"],
    "minfa-wuquan-qita": ["民法典"],
    "minfa-hetong": ["民法典"],
    "minfa-qinquan": ["民法典"],
    "minfa-hunyin": ["民法典"],
    # 刑法
    "xingfa": ["刑法"],
    "xingfa-zongze": ["刑法"],
    "xingfa-renshen": ["刑法"],
    "xingfa-caichan": ["刑法"],
    "xingfa-jingji": ["刑法"],
    "xingfa-gonggong": ["刑法"],
    "xingfa-tanbui": ["刑法"],
    "xingfa-duzhi": ["刑法"],
    # 民诉
    "minsusong": ["民事诉讼法"],
    "minsusong-guanxia": ["民事诉讼法"],
    "minsusong-dangshiren": ["民事诉讼法"],
    "minsusong-zhengju": ["民事诉讼法"],
    "minsusong-chengxu": ["民事诉讼法"],
    "minsusong-zhixing": ["民事诉讼法"],
    "minsusong-zhongcai": ["民事诉讼法"],
    # 刑诉
    "xingsusong": ["刑事诉讼法"],
    "xingsusong-yuanze": ["刑事诉讼法"],
    "xingsusong-chengxu": ["刑事诉讼法"],
    "xingsusong-zhengju": ["刑事诉讼法"],
    "xingsusong-bianhu": ["刑事诉讼法"],
    "xingsusong-qiangzhi": ["刑事诉讼法"],
    "xingsusong-zhixing": ["刑事诉讼法"],
    # 行政法
    "xingzhengfa": ["行政处罚法", "行政许可法", "行政强制法", "行政复议法", "行政诉讼法", "国家赔偿法"],
    "xingzhengfa-zonglun": ["行政处罚法", "行政许可法", "行政强制法"],
    "xingzhengfa-xingwei": ["行政处罚法", "行政许可法", "行政强制法"],
    "xingzhengfa-xinxi": ["行政处罚法", "行政许可法", "行政强制法"],
    "xingzhengfa-fuyi": ["行政复议法", "行政诉讼法"],
    "xingzhengfa-susong": ["行政诉讼法"],
    "xingzhengfa-peichang": ["国家赔偿法"],
    # 商经
    "shangjing": ["公司法", "证券法", "企业破产法", "反垄断法", "合伙企业法", "劳动合同法", "环境保护法"],
    "shangjing-gongsi": ["公司法"],
    "shangjing-hehuo": ["合伙企业法"],
    "shangjing-qiye": ["企业破产法", "反垄断法"],
    "shangjing-zhengquan": ["证券法"],
    "shangjing-laodong": ["劳动合同法"],
    "shangjing-huanjing": ["环境保护法"],
    # 理论法
    "lilunfa": ["宪法"],
    "lilunfa-falixue": ["宪法"],
    "lilunfa-xianfa": ["宪法"],
    "lilunfa-fazhisi": ["宪法"],
    "lilunfa-sifa": ["宪法"],
    # 三国法
    "sanguofa": ["涉外民事关系法律适用法", "联合国国际货物销售合同公约", "维也纳外交关系公约"],
    "sanguofa-gongfa": ["维也纳外交关系公约"],
    "sanguofa-sifa": ["涉外民事关系法律适用法"],
    "sanguofa-jingjifa": ["联合国国际货物销售合同公约"],
    # 工具页
    "kaoshi-zonglan": ["宪法"],
    "beikao-shijianbiao": [],
}


def build_block(laws):
    lines = [
        "",
        "## 相关权威链接",
        "",
        "> 备考提示：以下为权威官方发布渠道，建议结合最新修正案与司法解释一并研读。",
        "",
        "- [中华人民共和国最高人民法院（官网）]({})".format(SUPREME_COURT),
    ]
    for law in laws:
        url = LAW_URLS[law]
        src = source_of(url)
        lines.append("- [《{}》全文（{}）]({})".format(law, src, url))
    lines.append("")
    return "\n".join(lines)


def main():
    topics_dir = os.path.abspath(TOPICS_DIR)
    files = sorted(f for f in os.listdir(topics_dir) if f.endswith(".md"))
    updated = 0
    skipped = 0
    missing = 0
    for fn in files:
        slug = fn[:-3]
        path = os.path.join(topics_dir, fn)
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        # 若已存在链接区块，则截断到该区块之前，便于用新格式覆盖重建
        if "## 相关权威链接" in content:
            content = content.split("## 相关权威链接", 1)[0].rstrip() + "\n"
        if slug not in MAPPING:
            print("  [未映射，跳过] {}".format(fn))
            missing += 1
            continue
        laws = MAPPING[slug]
        # 校验链接存在
        for law in laws:
            if law not in LAW_URLS:
                raise SystemExit("法律 {} 缺少 URL，请补充后重试".format(law))
        block = build_block(laws)
        # 确保文末有空行
        if not content.endswith("\n"):
            content += "\n"
        content = content.rstrip("\n") + block
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        updated += 1
        print("  [已处理] {}  (+{} 法律链接)".format(fn, len(laws)))
    print("\n完成：处理 {} 个，未映射 {} 个，共扫描 {} 个文件。".format(
        updated, missing, len(files)))


if __name__ == "__main__":
    main()
