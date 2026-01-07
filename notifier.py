import subprocess
import os
import shutil


def send_notification(title: str, message: str, subtitle: str = "", sound: str = "default", open_url: str = None):
    tn = shutil.which("terminal-notifier") or "/opt/homebrew/bin/terminal-notifier"
    if tn and os.path.exists(tn):
        args = [tn, "-title", title, "-message", message]
        if subtitle:
            args += ["-subtitle", subtitle]
        if open_url:
            args += ["-open", open_url]
        try:
            subprocess.run(args, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    subtitle_part = f'subtitle "{subtitle}"' if subtitle else ""
    script = f'''
    display notification "{message}" with title "{title}" {subtitle_part} sound name "{sound}"
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def send_analysis_complete_notification(recommendation_count: int, accuracy_rate: float = None, report_path: str = None):
    title = "每日股票分析完成"
    if accuracy_rate is not None:
        message = f"今日推荐{recommendation_count}只股票，历史准确率{accuracy_rate:.0%}"
    else:
        message = f"今日推荐{recommendation_count}只股票"
    subtitle = "点击查看详细报告"
    open_url = f"file://{report_path}" if report_path else None
    return send_notification(title, message, subtitle, sound="Glass", open_url=open_url)


def send_error_notification(error_msg: str):
    return send_notification(title="股票分析出错", message=error_msg[:100], sound="Basso")


if __name__ == "__main__":
    # 测试通知
    send_notification("测试通知", "这是一条测试消息", "副标题测试")
