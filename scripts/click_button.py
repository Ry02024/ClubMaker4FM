import cv2
import numpy as np
import pyautogui
import time
import os

def click_template(template_path, confidence=0.8):
    if not os.path.exists(template_path):
        print(f"Error: Template image not found at {template_path}")
        return False

    # 現在の画面を撮影
    screenshot = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    # テンプレート画像を読み込み
    template = cv2.imread(template_path)
    h, w = template.shape[:2]

    # テンプレートマッチング実行
    res = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    print(f"Match confidence for {os.path.basename(template_path)}: {max_val:.4f}")

    if max_val >= confidence:
        # 中央の座標を計算
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        
        print(f"Found match! Clicking at ({center_x}, {center_y})")
        pyautogui.click(center_x, center_y)
        return True
    else:
        print("Match not found (low confidence).")
        return False

if __name__ == "__main__":
    # 使用例: python click_button.py assets/tc_button.png
    import sys
    if len(sys.argv) > 1:
        click_template(sys.argv[1])
    else:
        print("Usage: python click_button.py <path_to_template_image>")
