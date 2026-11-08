"""Trusted GitHub-side preparation and publication for the review workflow."""
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO = "Rookie-YCLin/matrix-jpeg-research"
OWNER = "Rookie-YCLin"
SMOKE_BRANCH = "codex/research-ai-review"
ROOT = Path(__file__).resolve().parents[2]
SHA = re.compile(r"[0-9a-f]{40}")
MARKER = re.compile(r"^<!-- research-ai-review:(live|smoke):([0-9a-f]{40}) -->")
ISSUE = re.compile(r"^(?:Research-Issue:\s*|對應\s*)#([1-9][0-9]{0,8})(?:[。.\s]|$)", re.M)
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "required", "suggestions", "decision", "basis"],
    "properties": {
        "status": {"type": "string", "enum": ["PASS", "NEEDS_CHANGES", "BLOCKED"]},
        "required": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
        "suggestions": {"type": "array", "items": {"$ref": "#/$defs/finding"}},
        "decision": {"type": "string"},
        "basis": {"type": "string"},
    },
    "$defs": {"finding": {
        "type": "object", "additionalProperties": False,
        "required": ["location", "problem", "evidence"],
        "properties": {key: {"type": "string"} for key in ("location", "problem", "evidence")},
    }},
}


def api(path, *, method="GET", data=None, max_bytes=4_000_000):
    request = Request(
        f"https://api.github.com/repos/{REPO}/{path}", method=method,
        headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json",
                 "X-GitHub-Api-Version": "2022-11-28"},
        data=json.dumps(data).encode() if data is not None else None,
    )
    with urlopen(request, timeout=25) as response:
        payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("GitHub response exceeded the byte limit")
    return json.loads(payload)


def output(**fields):
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as file:
        for key, value in fields.items():
            # Serialize multiline/untrusted inputs as one JSON line.
            if "\n" in str(value) or "\r" in str(value):
                raise ValueError("Unsafe workflow output")
            file.write(f"{key}={value}\n")


def trusted_pr(pr, branch, head):
    return (
        pr["state"] == "open" and pr["base"]["ref"] == "main"
        and pr["base"]["repo"]["full_name"] == REPO
        and (pr["head"]["repo"] or {}).get("full_name") == REPO
        and pr["head"]["ref"] == branch and pr["head"]["sha"] == head
        and pr["user"]["login"] == OWNER
    )


def target(event_name, event):
    if event_name == "push":
        if event.get("ref") != f"refs/heads/{SMOKE_BRANCH}" or event.get("deleted"):
            return None
        branch, head, mode = SMOKE_BRANCH, event["after"], "smoke"
    else:
        run = event["workflow_run"]
        if (run["event"] != "pull_request"
                or run["path"] != ".github/workflows/research-ci.yml"
                or (run.get("head_repository") or {}).get("full_name") != REPO
                or run["actor"]["login"] != OWNER
                or run["run_attempt"] != 1):
            return None
        branch, head, mode = run["head_branch"], run["head_sha"], "live"
    if mode == "smoke" and event["sender"]["login"] != OWNER:
        return None
    if not isinstance(branch, str) or not SHA.fullmatch(head):
        return None
    query = urlencode({"state": "open", "base": "main", "head": f"{OWNER}:{branch}"})
    prs = api(f"pulls?{query}")
    matches = [pr for pr in prs if trusted_pr(pr, branch, head)]
    if len(matches) != 1:
        return None
    return matches[0], mode


def scope(pr):
    ids = set(ISSUE.findall(pr.get("body") or ""))
    if len(ids) != 1:
        raise ValueError("需要在 PR 說明指定唯一 Research-Issue: #N")
    number = int(ids.pop())
    try:
        issue = api(f"issues/{number}")
    except HTTPError as exc:
        if exc.code == 404:
            raise ValueError("研究 Issue 不存在") from None
        raise
    if ("pull_request" in issue or issue["state"] != "open"
            or issue["user"]["login"] != OWNER):
        raise ValueError("研究 Issue 必須開啟且由研究主持人建立")
    body = (issue["body"] or "").split("<details>", 1)[0]
    if not body.strip() or len(body.encode()) > 12_000:
        raise ValueError("研究 Issue 規格缺失或超過審查容量")
    return number, body


def context(pr, ci):
    number, body = scope(pr)
    base, head = pr["base"]["sha"], pr["head"]["sha"]
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):
        raise ValueError("Invalid commit")
    comparison = api(f"compare/{base}...{head}?per_page=1")
    files = comparison["files"]
    if not files or len(files) >= 300 or len(files) != pr["changed_files"]:
        raise ValueError("無法完整取得比較檔案")
    if any(item.get("additions", 0) + item.get("deletions", 0) and not item.get("patch")
           for item in files):
        raise ValueError("文字差異缺失，需人工審查")
    if any(sum(line.startswith(("+", "-")) for line in item["patch"].splitlines())
           != item["additions"] + item["deletions"] for item in files if item.get("patch")):
        raise ValueError("文字差異遭截斷，需人工審查")
    data = {
        "issue_number": number, "issue_body": body, "base": base, "head": head,
        "ci_conclusion": ci,
        "files": [{key: item.get(key) for key in ("filename", "previous_filename", "status", "patch")}
                  for item in files],
    }
    payload = json.dumps(data, ensure_ascii=False)
    if len(payload.encode()) > 48_000:
        raise ValueError("差異超出審查容量，請拆分 PR 或安排人工審查")
    return payload


def blocked(reason):
    return {"status": "BLOCKED", "required": [{"location": "—", "problem": reason,
                                             "evidence": "工作流程未取得可用的模型審查。"}],
            "suggestions": [], "basis": "沒有可驗證的模型判定。", "decision": "是，請主持人確認阻礙後再安排審查。"}


def validate(report):
    if (not isinstance(report, dict) or report.keys() != set(SCHEMA["required"])
            or report["status"] not in ("PASS", "NEEDS_CHANGES", "BLOCKED")
            or not isinstance(report["decision"], str) or not report["decision"].strip()
            or len(report["decision"]) > 400
            or not isinstance(report["basis"], str) or not report["basis"].strip()
            or len(report["basis"]) > 1500):
        raise ValueError("Invalid review structure")
    for group in ("required", "suggestions"):
        if not isinstance(report[group], list) or len(report[group]) > 8:
            raise ValueError("Invalid finding list")
        for finding in report[group]:
            if (not isinstance(finding, dict) or finding.keys() != {"location", "problem", "evidence"}
                    or any(not isinstance(value, str) or not value.strip() or len(value) > 1000
                           for value in finding.values())):
                raise ValueError("Invalid finding")
    if bool(report["required"]) != (report["status"] != "PASS"):
        raise ValueError("Status disagrees with findings")
    return report


def comment(mode, head, report, source):
    validate(report)
    lines = [
        f"<!-- research-ai-review:{mode}:{head} -->",
        f"## 研究審查 · {report['status']}", "",
        f"提交 SHA：\x60{head}\x60  ",
        f"來源：{source}  ",
        f"執行紀錄：https://github.com/{REPO}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    ]
    lines += ["", "### 數學與實驗依據", "", "    " + " ".join(report["basis"].split())]
    for key, title in (("required", "必須修改或解除的阻礙"), ("suggestions", "建議改善")):
        lines += ["", f"### {title}", ""]
        if not report[key]:
            lines.append("無。")
        for finding in report[key]:
            # Indented code makes Markdown, HTML, links and mentions inert.
            for field, label in (("location", "位置"), ("problem", "問題"), ("evidence", "依據")):
                lines.append(f"    {label}：{' '.join(finding[field].split())}")
            lines.append("")
    lines += ["", "### 研究主持人決策", "", f"    {' '.join(report['decision'].split())}"]
    return "\n".join(lines)


def prepare():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    selected = target(os.environ["GITHUB_EVENT_NAME"], event)
    if selected is None:
        return
    pr, mode = selected
    number, head = pr["number"], pr["head"]["sha"]
    comments = api(f"issues/{number}/comments?per_page=100")
    if len(comments) >= 100:
        return  # Conservative when the review history may be incomplete.
    markers = [match.groups() for item in comments
               if item["user"]["login"] == "github-actions[bot]"
               if (match := MARKER.match(item["body"]))]
    if (mode, head) in markers or sum(kind == mode for kind, _ in markers) >= 3:
        return

    if mode == "smoke":
        reason = "受控無金鑰測試，未呼叫模型。"
        prompt = ""
    else:
        try:
            detail = api(f"pulls/{number}")
            if not trusted_pr(detail, pr["head"]["ref"], head) or detail["base"]["sha"] != pr["base"]["sha"]:
                return
            prompt = context(detail, event["workflow_run"]["conclusion"])
            reason = ""
        except ValueError as exc:
            prompt, reason = "", str(exc)

    current = api(f"pulls/{number}")
    if not trusted_pr(current, pr["head"]["ref"], head) or current["base"]["sha"] != pr["base"]["sha"]:
        return
    reservation = api(f"issues/{number}/comments", method="POST",
                      data={"body": comment(mode, head, blocked(reason or "模型審查尚未完成。"),
                                            "GitHub Actions 預檢")})
    output(reservation=reservation["id"], number=number, head=head, branch=pr["head"]["ref"],
           mode=mode, base=current["base"]["sha"], reason=json.dumps(reason, ensure_ascii=False),
           prompt=json.dumps(prompt, ensure_ascii=False),
           schema=json.dumps(SCHEMA, ensure_ascii=False),
           policy=json.dumps((ROOT / "AI_REVIEW_POLICY.md").read_text(encoding="utf-8"),
                             ensure_ascii=False))


def publish():
    number, reservation = int(os.environ["PR_NUMBER"]), int(os.environ["RESERVATION"])
    head, branch, mode = (os.environ[key] for key in ("HEAD_SHA", "HEAD_BRANCH", "REVIEW_MODE"))
    current = api(f"pulls/{number}")
    if not trusted_pr(current, branch, head) or current["base"]["sha"] != os.environ["BASE_SHA"]:
        return  # The reservation remains a SHA-bound historical record.
    existing = api(f"issues/comments/{reservation}")
    if (existing["user"]["login"] != "github-actions[bot]"
            or existing["issue_url"].rsplit("/", 1)[-1] != str(number)
            or not existing["body"].startswith(f"<!-- research-ai-review:{mode}:{head} -->")):
        raise ValueError("Invalid review reservation")
    reason = json.loads(os.environ["BLOCK_REASON"])
    source = "GitHub Actions 預檢"
    if mode == "smoke":
        report = blocked(reason)
        source = "GitHub Actions 無金鑰驗證"
    else:
        try:
            if reason or os.environ["MODEL_RESULT"] != "success":
                raise ValueError("Review unavailable")
            report = validate(json.loads(os.environ["MODEL_MESSAGE"]))
            source = "OpenAI Codex GitHub Action"
        except (ValueError, TypeError):
            report = blocked(reason or "模型未完成或輸出無效，請查閱執行紀錄與審查環境設定。")
    api(f"issues/comments/{reservation}", method="PATCH",
        data={"body": comment(mode, head, report, source)})


if __name__ == "__main__":
    try:
        {"prepare": prepare, "publish": publish}[sys.argv[1]]()
    except HTTPError as exc:
        sys.exit(f"GitHub API HTTP {exc.code}")
