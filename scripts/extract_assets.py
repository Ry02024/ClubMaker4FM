from PIL import Image
import os

def crop_assets(source_image_path, target_dir="assets"):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    img = Image.open(source_image_path)
    
    # ユーザー画像 (1046x785想定) から「貼り付け(I)」ボタンを抽出
    # 座標は目視での見積もり。
    # 貼り付け(I) ボタン付近
    paste_btn = img.crop((860, 735, 950, 765))
    paste_btn.save(os.path.join(target_dir, "paste_button.png"))
    
    # 作成(E) ボタン
    create_btn = img.crop((170, 735, 265, 765))
    create_btn.save(os.path.join(target_dir, "create_button.png"))
    
    print(f"Assets cropped and saved to {target_dir}")

if __name__ == "__main__":
    source = r"C:\Users\81909\.gemini\antigravity\brain\769d92d4-54d1-484a-bccc-84e7893c8d09\uploaded_image_1768611846133.png"
    crop_assets(source)
