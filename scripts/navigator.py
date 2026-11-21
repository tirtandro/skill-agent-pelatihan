import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner

runner = AgentDesktopRunner()

def find_chrome_window():
    res = runner.run(['list-windows'])
    windows = res.get('data', [])
    for w in windows:
        if 'chrome.exe' in w.get('app_name', '').lower() and 'pelatihan mandiri' in w.get('title', '').lower():
            return w.get('id')
    for w in windows:
        if 'chrome.exe' in w.get('app_name', '').lower():
            return w.get('id')
    return 'w-132020'

def navigate_to(url, window_id=None, wait_seconds=3):
    if not window_id:
        window_id = find_chrome_window()
    runner.run(['focus-window', '--window-id', window_id])
    runner.run(['clipboard-set', url])
    runner.run(['press', '--headed', 'ctrl+l'])
    time.sleep(0.15)
    runner.run(['press', '--headed', 'ctrl+v'])
    time.sleep(0.15)
    runner.run(['press', '--headed', 'return'])
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    # Release omnibox focus trap
    runner.run(['press', '--headed', 'escape'])
    time.sleep(0.2)
    runner.run(['mouse-click', '--headed', '--xy=-540,500'])

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/topik/1'
    win = sys.argv[2] if len(sys.argv) > 2 else None
    navigate_to(url, window_id=win)
    print("Navigated safely to:", url)
